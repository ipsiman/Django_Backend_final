from django.test import TestCase, Client
from django.urls import reverse
from posts.models import Post, Group, User
from django.core.cache import cache


class PostTests(TestCase):
    def setUp(self):
        cache.clear()
        self.no_auth_client = Client()
        self.auth_client = Client()
        self.auth_client2 = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.ru',
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@test.ru',
        )
        self.group = Group.objects.create(
            title='test',
            slug='test_group',
            description='empty'
        )
        self.auth_client.force_login(self.user)
        self.auth_client2.force_login(self.user2)

    def create_post(self):
        return Post.objects.create(
            text='test text new post',
            author=self.user,
            group=self.group)

    def create_post_with_image(self, image):
        return Post.objects.create(
            text='test text new post with image',
            author=self.user,
            group=self.group,
            image=image)

    def check_text_in_url(self, text):
        for url in (
            reverse('index'),
            reverse('profile', kwargs={'username': self.user.username}),
            reverse('post_view', kwargs={'username': self.user.username,
                                         'post_id': self.post.id})):
            response = self.auth_client.get(url)
            return self.assertContains(response, text)

    def test_profile(self):
        response = self.no_auth_client.get(
            reverse('profile', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 200)

    def test_no_auth_new_post(self):
        response = self.no_auth_client.post(
            reverse('new_post'), data={'text': 'test text'})
        self.assertNotEqual(response.status_code, 200)
        self.assertRedirects(response, '/auth/login/?next=/new')

    def test_auth_new_post(self):
        response = self.auth_client.post(
            reverse('new_post'),
            data={'text': 'test text new post', 'group': self.group.id},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Post.objects.filter(
            text='test text new post', group=self.group.id).exists()
        )

    def test_view_auth_post(self):
        self.post = self.create_post()
        self.check_text_in_url('test text new post')

    def test_edit_auth_post(self):
        self.post = self.create_post()
        response = self.auth_client.get(reverse('post_edit', kwargs={
            'username': self.user.username, 'post_id': self.post.id}))
        self.assertEqual(response.status_code, 200)
        self.post.text = 'test edited text'
        self.post.save()
        self.check_text_in_url('test edited text')
        self.assertTrue(Post.objects.filter(
            text='test edited text',
            group=self.group.id,
            author=self.user).exists())

    def test_image_in_urls(self):
        self.post = self.create_post_with_image('test_img.png')
        self.check_text_in_url('<img')

    def test_post_with_image(self):
        with open('media/test_img.png', 'rb') as img:
            response = self.auth_client.post(
                reverse('new_post'),
                data={'text': 'image', 'group': self.group.id, 'image': img},
                follow=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, '<img')
            self.assertEqual(Post.objects.count(), 1)

    def test_not_image_upload(self):
        with open('media/test.txt', 'rb') as img:
            response = self.auth_client.post(
                reverse('new_post'),
                data={'text': 'image', 'group': self.group.id, 'image': img},
                follow=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(Post.objects.count(), 0)

    def test_cache_index(self):
        self.auth_client.get(reverse('index'))
        self.auth_client.post(
            reverse('new_post'),
            data={'text': 'test cache', 'group': self.group.id},
            follow=True)
        response = self.auth_client.get(reverse('index'))
        self.assertNotContains(response, 'test cache')

    def test_auth_follow_unfollow(self):
        self.auth_client.get(reverse('profile_follow', kwargs={'username': self.user2.username}))
        self.assertEqual(self.user.follower.count(), 1)
        self.auth_client.get(reverse('profile_unfollow', kwargs={'username': self.user2.username}))
        self.assertEqual(self.user.follower.count(), 0)


class ServerErrorsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_404(self):
        response = self.client.get('/nohaveadminpage/posts')
        self.assertEqual(response.status_code, 404)
