from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .forms import PublicBlogPostForm
from .models import BlogPost


def new_post(request):
    """Create a new blog post awaiting editorial review.
    """
    if not request.user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)
    if request.method == 'POST':
        form = PublicBlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog:index')
    else:
        form = PublicBlogPostForm()
    return render(request, 'blog/new_post.html', {'form': form})


def post_list(request):
    """Render the public blog index showing published posts.

    Only posts that are published and approved are shown, ordered by
    published_at.
    """
    posts = BlogPost.published.order_by('-published_at')
    return render(request, 'blog/index.html', {'posts': posts})


def post_detail(request, year, month, day, slug):
    """Render a single blog post by date and slug.

    Only published & approved posts are shown to anonymous users. Authors can
    view their own drafts when logged in.
    """
    qs = BlogPost.objects.filter(slug=slug)
    qs = qs.filter(published_at__year=year,
                   published_at__month=month, published_at__day=day)
    post = get_object_or_404(qs)
    if (post.status != 'published' or not post.is_approved) and request.user != post.author:
        return HttpResponse('Not found', status=404)
    return render(request, 'blog/post_detail.html', {'post': post})
