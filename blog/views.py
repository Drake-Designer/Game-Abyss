from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .forms import PublicBlogPostForm, CommentForm
from .models import BlogPost, Comment


def new_post(request):
    """Launch a new signal into the Abyss: staff goes live, explorers queue in orbit (pending)."""
    # Gatekeeper: no ghosts past this point.
    if not request.user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)

    if request.method == 'POST':
        form = PublicBlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            # Forge the payload without committing it to the void yet.
            post = form.save(commit=False)
            post.author = request.user

            # Staff captains skip the orbit and land on the front page.
            if request.user.is_staff:
                post.status = BlogPost.STATUS_APPROVED
                messages.success(
                    request, "Deployed. Your post is live on the front page.")
            else:
                # Regular explorers drift in review orbit until cleared by the Council.
                post.status = BlogPost.STATUS_PENDING
                messages.info(
                    request,
                    "Transmission received. Your post is in review and will surface once approved.",
                )

            # Release the capsule into the Abyss.
            post.save()
            return redirect('blog:index')
    else:
        # Empty hull for a fresh launch sequence.
        form = PublicBlogPostForm()

    return render(request, 'blog/new_post.html', {'form': form})


def post_list(request):
    """Surface-level index: only signals approved by the Council breach the Abyss."""
    # Pull only approved echoes, sorted by most recently surfaced.
    posts = BlogPost.approved.order_by('-published_at', '-updated_at')
    return render(request, 'blog/index.html', {'posts': posts})


def post_detail(request, year, month, day, slug):
    """Deep-scan a single signal; only stable (approved) transmissions are public."""
    # Lock onto a specific echo in spacetime.
    qs = BlogPost.objects.filter(slug=slug)
    qs = qs.filter(
        published_at__year=year,
        published_at__month=month,
        published_at__day=day,
    )
    post = get_object_or_404(qs)

    # If the signal isn't cleared for the public, only the owner can view it.
    if (post.status != BlogPost.STATUS_APPROVED) and request.user != post.author:
        return HttpResponse('Not found', status=404)

    # Only comments that escaped moderation orbit appear in the feed.
    approved_comments = post.comments.approved()
    comment_form = CommentForm()

    # Handle new comment transmissions from explorers.
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if not request.user.is_authenticated:
            messages.error(
                request, 'Log in to add your signal to the constellation.')
        elif comment_form.is_valid():
            # Stage the comment for orbit: pending by default until cleared.
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.status = Comment.STATUS_PENDING
            comment.save()
            messages.success(
                request,
                "Thanks, explorer. Your comment is in orbit and will appear after approval.",
            )
            return redirect(post.get_absolute_url())

    context = {
        'post': post,
        'comments': approved_comments,
        'comment_form': comment_form,
    }
    return render(request, 'blog/post_detail.html', context)
