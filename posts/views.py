from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator
from .models import Post, Group, User
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
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'profile.html',
        {'page': page,
         'paginator': paginator,
         'author': author,
         }
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    author = post.author
    post_count = author.posts.count()
    form = CommentForm()
    items = post.comments.all()
    return render(
        request,
        'post.html',
        {'post_count': post_count,
         'author': author,
         'post': post,
         'items': items,
         'form': form,
         }
    )


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    author = post.author
    if not author == request.user:
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


def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect('post_view', username=username, post_id=post_id)
    return render(request, 'post.html', {'form': form})

