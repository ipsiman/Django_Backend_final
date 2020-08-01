from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.group.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'group.html',
        {'group': group, 'page': page, 'paginator': paginator}
    )


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    return render(
            request,
            'new.html',
            {'form': form,
             'title_str': 'Новая запись',
             'header_str': 'Новая запись',
             'button_str': 'Опубликовать'
             }
        )


def profile(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    post_count = paginator.count
    follower_count = author.follower.count()
    following_count = author.following.count()
    following = (
        request.user.is_authenticated
        and Follow.objects.filter(user=user, author=author).exists()
    )
    return render(
        request,
        'profile.html',
        {'page': page,
         'paginator': paginator,
         'author': author,
         'following': following,
         'follower_count': follower_count,
         'following_count': following_count,
         'post_count': post_count,
         }
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    author = post.author
    user = request.user
    post_count = author.posts.count()
    follower_count = author.follower.count()
    following_count = author.following.count()
    form = CommentForm()
    following = False
    if user.is_authenticated:
        if user.follower.filter(user=user, author=author).exists():
            following = True
    items = post.comments.all()
    return render(
        request,
        'post.html',
        {'post_count': post_count,
         'author': author,
         'post': post,
         'items': items,
         'form': form,
         'following': following,
         'follower_count': follower_count,
         'following_count': following_count,
         'user': user,
         }
    )


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    author = post.author
    if author != request.user:
        return redirect(
            'post_view',
            username=author.username,
            post_id=post.id
        )
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        post = form.save(commit=False)
        post.save()
        return redirect(
            'post_view',
            username=author.username,
            post_id=post.id
        )
    return render(
        request,
        'new.html',
        {'form': form,
         'post': post,
         'title_str': 'Редактирование записи',
         'header_str': 'Редактирование записи',
         'button_str': 'Сохранить'
         }
    )


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect('post_view', username=username, post_id=post_id)
    return redirect('post_view', post_id=post_id, username=username)


@login_required
def follow_index(request):
    user_follows = (
        User
        .objects
        .get(id=request.user.id)
        .follower
        .all()
        .values_list('author')
    )
    post_list = Post.objects.filter(author__in=user_follows)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'follow.html',
        {'page': page, 'paginator': paginator}
    )


@login_required
def profile_follow(request, username):
    author = User.objects.get(username=username)
    user = request.user
    if user != author:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = User.objects.get(username=username)
    Follow.objects.filter(user=request.user, author=author,).delete()
    return redirect('profile', username=username)