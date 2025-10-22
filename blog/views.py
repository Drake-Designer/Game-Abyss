from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .forms import PublicBlogPostForm, CommentForm
from .models import BlogPost, Comment


def new_post(request):
    """Create a new blog post awaiting editorial review."""
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
    """Render the public blog index showing approved posts ordered by date."""
    posts = BlogPost.approved.order_by('-published_at', '-updated_at')
    return render(request, 'blog/index.html', {'posts': posts})


def post_detail(request, year, month, day, slug):
    """Render a single blog post by date and slug.

    Anonymous users only see approved and published posts.
    Authors can view their own drafts when authenticated.
    """
    qs = BlogPost.objects.filter(slug=slug)
    qs = qs.filter(
        published_at__year=year,
        published_at__month=month,
        published_at__day=day,
    )
    post = get_object_or_404(qs)

    if (post.status != BlogPost.STATUS_APPROVED) and request.user != post.author:
        return HttpResponse('Not found', status=404)

    approved_comments = post.comments.approved()
    comment_form = CommentForm()

    # Handle public comment submission
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if not request.user.is_authenticated:
            messages.error(
                request, 'You must be logged in to submit a comment.')
        elif comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.status = Comment.STATUS_PENDING
            comment.save()
            messages.success(
                request,
                "Thanks. Your comment will appear once it has been approved.",
            )
            return redirect(post.get_absolute_url())

    context = {
        'post': post,
        'comments': approved_comments,
        'comment_form': comment_form,
    }
    return render(request, 'blog/post_detail.html', context)
