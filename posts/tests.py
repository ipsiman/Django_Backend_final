import io
import tempfile
from unittest import mock

from PIL import Image
from django.core.files import File
from django.core.files.base import ContentFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from posts.models import Post, Group, User
from django.core.cache import cache


class PostTests(TestCase):
    def setUp(self):
        cache.clear()
        self.no_auth_client = Client()
        self.auth_client = Client()
        self.auth_client2 = Client()
        self.auth_client3 = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.ru',
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@test.ru',
        )
        self.user3 = User.objects.create_user(
            username='testuser3',
            email='test3@test.ru',
        )
        self.group = Group.objects.create(
            title='test',
            slug='test_group',
            description='empty'
        )
        self.auth_client.force_login(self.user)
        self.auth_client2.force_login(self.user2)
        self.auth_client3.force_login(self.user3)

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
        author = self.post.author
        group = self.post.group
        for url in (
            reverse('index'),
            reverse('profile', kwargs={'username': self.user.username}),
            reverse('post_view', kwargs={'username': self.user.username,
                                         'post_id': self.post.id})):
            with self.subTest(url=url):
                response = self.auth_client.get(url)
                #  проверку паджинатора убрал - его нет на странице с постом
                self.assertContains(response, text),
                self.assertEqual(response.context['post'].author, author),
                self.assertEqual(response.context['post'].group, group)

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
        with tempfile.TemporaryDirectory() as temp_directory:
            with override_settings(MEDIA_ROOT=temp_directory):
                byte_img = io.BytesIO()
                im = Image.new("RGB", size=(500, 500), color=(255, 0, 0, 0))
                im.save(byte_img, format='png')
                byte_img.seek(0)
                response = self.auth_client.post(
                    reverse('new_post'),
                    data={'text': 'image',
                          'group': self.group.id,
                          'image': ContentFile(byte_img.read(), name='t.png')},
                    follow=True
                )
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, '<img')
                self.assertEqual(Post.objects.count(), 1)

    def test_not_image_upload(self):
        error_text = (
            'Загрузите правильное изображение.'
            ' Файл, который вы загрузили, поврежден'
            ' или не является изображением.'
        )
        file_mock = mock.MagicMock(spec=File, name='test.txt')
        response = self.auth_client.post(
            reverse('new_post'),
            data={'text': 'image', 'group': self.group.id, 'image': file_mock},
            follow=True
        )
        self.assertFormError(response, form='form', field='image',
                             errors=error_text)
        self.assertEqual(Post.objects.count(), 0)

    def test_cache_index(self):
        self.auth_client.get(reverse('index'))
        self.auth_client.post(
            reverse('new_post'),
            data={'text': 'test cache', 'group': self.group.id},
            follow=True)
        response = self.auth_client.get(reverse('index'))
        self.assertNotContains(response, 'test cache')

    def test_auth_follow(self):
        self.assertEqual(self.user.follower.count(), 0)
        self.auth_client.get(reverse('profile_follow',
                                     kwargs={'username': self.user2.username}))
        self.assertEqual(self.user.follower.count(), 1)

    def test_auth_unfollow(self):
        self.auth_client.get(reverse('profile_follow',
                                     kwargs={'username': self.user2.username}))
        self.assertEqual(self.user.follower.count(), 1)
        self.auth_client.get(reverse('profile_unfollow',
                                     kwargs={'username': self.user2.username}))
        self.assertEqual(self.user.follower.count(), 0)


    def test_add_comment(self):
        post = self.create_post()
        self.auth_client.post(reverse('add_comment',
                                      kwargs={'username': post.author.username,
                                              'post_id': post.id}),
                              data={'post': post,
                                    'author': post.author.username,
                                    'text': 'new test comment'}, follow=True)
        self.assertEqual(post.comments.count(), 1)

    def test_no_auth_add_comment(self):
        post = self.create_post()
        response = self.no_auth_client.post(
            reverse('add_comment', kwargs={'username': post.author.username,
                                           'post_id': post.id}),
            data={'post': post, 'author': post.author.username,
                  'text': 'new test comment'})
        self.assertEqual(post.comments.count(), 0)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f'/auth/login/?next=/{post.author.username}/{post.id}/comment')

    def test_follow_post(self):
        self.create_post()
        self.auth_client2.get(reverse(
            'profile_follow', kwargs={'username': self.user.username}))
        response = self.auth_client.get(reverse('follow_index'))
        response2 = self.auth_client2.get(reverse('follow_index'))
        response3 = self.auth_client3.get(reverse('follow_index'))
        self.assertNotContains(response, 'test text new post')
        self.assertContains(response2, 'test text new post')
        self.assertNotContains(response3, 'test text new post')


class ServerErrorsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_404(self):
        response = self.client.get('/nohaveadminpage/posts')
        self.assertEqual(response.status_code, 404)
