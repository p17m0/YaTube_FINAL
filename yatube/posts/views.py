from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from yatube.settings import QUANTITY

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow


def pagina(request, posts):
    paginator = Paginator(posts, QUANTITY)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


@cache_page(60 * 0.25)
def index(request):
    posts = Post.objects.all()
    context = {
        'page_obj': pagina(request, posts),
    }
    return render(request, 'posts/index.html', context)


def posts_group(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    context = {
        'group': group,
        'page_obj': pagina(request, posts),
    }
    return render(request, 'posts/group_list.html', context)


@login_required
def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    if author.following.filter(user=request.user).exists():
        context = {
            'author': author,
            'page_obj': pagina(request, posts),
            'following': True,
        }
        return render(request, 'posts/profile.html', context)
    else:
        context = {
            'author': author,
            'page_obj': pagina(request, posts),
            'following': False,
        }
        return render(request, 'posts/profile.html', context)


@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    # List of active comments for this post
    comments = post.comments.all()
    comment_form = CommentForm(request.POST or None)
    return render(request,
                  'posts/post_detail.html', {'post': post,
                                             'comments': comments,
                                             'form': comment_form})


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    context = {'form': form}
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user.username)
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if post.author == request.user and form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, 'posts/create_post.html',
                  {'is_edit': True, 'form': form, })


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(request, 'posts/post_detail.html', {'post': post,
                                                      'comments': comments,
                                                      'form': form})


@login_required
def follow_index(request):
    if len(Follow.objects.filter(user=request.user)) == 0:
        context = {'page_obj': None}
        return render(request, 'posts/follow.html', context)
    else:
        follower = Follow.objects.get(user=request.user)
        posts = follower.author.posts.all()
        context = {'page_obj': pagina(request, posts)}
        return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = User.objects.get(username=username)
    user = request.user
    if author != user:
        follow = Follow(author=author, user=user)
        if len(Follow.objects.filter(author=author, user=user)) == 0:
            follow.save()
        return redirect('posts:profile', username=username)
    else:
        return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = User.objects.get(username=username)
    follower = Follow.objects.get(author=author,
                                  user=request.user)
    follower.delete()
    return redirect('posts:profile', username=username)
