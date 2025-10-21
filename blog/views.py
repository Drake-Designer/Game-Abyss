from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .forms import BlogPostForm
from .models import BlogPost


def new_post(request):
    """Create a new blog post.

    GET: show an empty BlogPostForm.
    POST: validate and save the post, assign the current user as author,
    then redirect to the public blog index so the post is visible.
    Returns 401 if the user is not authenticated.
    """
    if not request.user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog:index')
    else:
        form = BlogPostForm()
    return render(request, 'blog/new_post.html', {'form': form})


def post_list(request):
    """Render the public blog index showing published posts.

    Only posts with status 'published' are shown, ordered by published_at.
    """
    posts = BlogPost.objects.filter(
        status='published').order_by('-published_at')
    return render(request, 'blog/index.html', {'posts': posts})


def post_detail(request, year, month, day, slug):
    """Render a single blog post by date and slug.

    Only published posts are shown to anonymous users. Authors can view
    their own drafts when logged in.
    """
    qs = BlogPost.objects.filter(slug=slug)
    # narrow by date
    qs = qs.filter(published_at__year=year,
                   published_at__month=month, published_at__day=day)
    post = get_object_or_404(qs)
    # if the post is draft and the user is not the author, block access
    if post.status != 'published' and request.user != post.author:
        return HttpResponse('Not found', status=404)
    return render(request, 'blog/post_detail.html', {'post': post})
