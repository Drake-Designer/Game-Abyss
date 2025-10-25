from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST

from .forms import PublicBlogPostForm, CommentForm
from .models import (
    BlogPost,
    Comment,
    CommentReaction,
    CommentReport,
    PostReaction,
    ReactionType,
)

# Icon map used by the template to render reaction buttons
REACTION_ICON_MAP = {
    ReactionType.LIKE.value: 'fa-thumbs-up',
    ReactionType.LOVE.value: 'fa-heart',
    ReactionType.DISLIKE.value: 'fa-thumbs-down',
}

# Options for rendering the reaction choices
REACTION_OPTIONS = [
    {
        'value': choice.value,
        'label': choice.label,
        'icon': REACTION_ICON_MAP[choice.value],
    }
    for choice in ReactionType
]

REACTION_VALUES = {opt['value'] for opt in REACTION_OPTIONS}


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
            if request.user.is_staff or request.user.is_superuser:
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

    # Prepare the comment form (for POST below) and list of approved comments.
    comment_form = CommentForm()

    if request.method == 'POST':
        # New comment submission
        comment_form = CommentForm(request.POST)
        if not request.user.is_authenticated:
            messages.error(
                request, 'Log in to add your signal to the constellation.')
        elif comment_form.is_valid():
            # Stage the comment for orbit: pending by default until cleared.
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            if request.user.is_staff or request.user.is_superuser:
                comment.status = Comment.STATUS_APPROVED
                comment.save()
                messages.success(
                    request,
                    "Comment deployed. It's live for all explorers.",
                )
            else:
                comment.status = Comment.STATUS_PENDING
                comment.save()
                messages.success(
                    request,
                    "Thanks, explorer. Your comment is in orbit and will appear after approval.",
                )
            return redirect(post.get_absolute_url())
        else:
            messages.error(
                request,
                'We could not accept that comment. Please review the highlighted issues.',
            )

    # Fetch comments and their related reactions/reports efficiently
    approved_comments = list(
        post.comments.approved()
        .select_related('author')
        .prefetch_related('reactions__user', 'reports__reported_by')
    )

    # Compute post reaction totals and current user's reaction
    post_reactions = list(post.reactions.select_related('user'))
    post_reaction_totals = {opt['value']: 0 for opt in REACTION_OPTIONS}
    for r in post_reactions:
        post_reaction_totals[r.reaction] = post_reaction_totals.get(
            r.reaction, 0) + 1

    user_post_reaction = None
    if request.user.is_authenticated:
        for r in post_reactions:
            if r.user_id == request.user.id:
                user_post_reaction = r.reaction
                break

    post_reaction_display = [
        {
            **opt,
            'count': post_reaction_totals.get(opt['value'], 0),
            'active': (opt['value'] == user_post_reaction),
        }
        for opt in REACTION_OPTIONS
    ]

    # For each comment, compute reaction totals and whether the current user reported it
    for c in approved_comments:
        totals = {opt['value']: 0 for opt in REACTION_OPTIONS}
        user_comment_reaction = None

        for r in c.reactions.all():
            totals[r.reaction] = totals.get(r.reaction, 0) + 1
            if request.user.is_authenticated and r.user_id == request.user.id:
                user_comment_reaction = r.reaction

        c.reaction_display = [
            {
                **opt,
                'count': totals.get(opt['value'], 0),
                'active': (opt['value'] == user_comment_reaction),
            }
            for opt in REACTION_OPTIONS
        ]

        c.can_delete = False
        c.can_report = False
        c.user_reported = False
        if request.user.is_authenticated:
            can_delete = request.user.is_staff or request.user == c.author
            c.can_delete = can_delete
            can_report = (not request.user.is_staff) and (
                request.user != c.author)
            c.can_report = can_report
            if can_report:
                for rep in c.reports.all():
                    if rep.reported_by_id == request.user.id:
                        c.user_reported = True
                        break

    context = {
        'post': post,
        'comments': approved_comments,
        'comment_form': comment_form,
        'post_reaction_display': post_reaction_display,
    }
    return render(request, 'blog/post_detail.html', context)


@login_required
@require_POST
def react_to_post(request, pk):
    """Add/replace/remove the current user's reaction on a post."""
    post = get_object_or_404(BlogPost, pk=pk)
    reaction_value = request.POST.get('reaction')
    redirect_url = request.POST.get('next') or post.get_absolute_url()

    if reaction_value not in REACTION_VALUES:
        messages.error(request, 'Invalid reaction.')
        return redirect(redirect_url)

    reaction, created = PostReaction.objects.get_or_create(
        post=post, user=request.user)

    # Toggle: if same reaction posted again, remove it
    if not created and reaction.reaction == reaction_value:
        reaction.delete()
        messages.info(request, 'Reaction removed.')
    else:
        reaction.reaction = reaction_value
        reaction.save(update_fields=['reaction', 'updated_at'])
        messages.success(request, 'Reaction recorded!')

    return redirect(redirect_url)


@login_required
@require_POST
def react_to_comment(request, pk):
    """Add/replace/remove the current user's reaction on a comment."""
    comment = get_object_or_404(Comment, pk=pk)
    redirect_url = request.POST.get(
        'next') or f"{comment.post.get_absolute_url()}#comment-{comment.pk}"

    # Only staff can react to non-approved comments
    if comment.status != Comment.STATUS_APPROVED and not request.user.is_staff:
        messages.error(request, 'You cannot react to a non-approved comment.')
        return redirect(redirect_url)

    reaction_value = request.POST.get('reaction')
    if reaction_value not in REACTION_VALUES:
        messages.error(request, 'Invalid reaction.')
        return redirect(redirect_url)

    reaction, created = CommentReaction.objects.get_or_create(
        comment=comment, user=request.user)

    # Toggle: if same reaction posted again, remove it
    if not created and reaction.reaction == reaction_value:
        reaction.delete()
        messages.info(request, 'Comment reaction removed.')
    else:
        reaction.reaction = reaction_value
        reaction.save(update_fields=['reaction', 'updated_at'])
        messages.success(request, 'Comment reaction recorded!')

    return redirect(redirect_url)


@login_required
@require_POST
def report_comment(request, pk):
    """Report a comment; if reported, the comment goes back to pending for moderation."""
    comment = get_object_or_404(Comment, pk=pk)
    redirect_url = request.POST.get(
        'next') or f"{comment.post.get_absolute_url()}#comment-{comment.pk}"

    if request.user.is_staff or request.user.is_superuser:
        return HttpResponseForbidden('Staff members cannot report comments.')

    if comment.author_id == request.user.id:
        messages.error(request, 'You cannot report your own comment.')
        return redirect(redirect_url)

    reason = request.POST.get('reason')
    notes = (request.POST.get('notes') or '').strip()

    if reason not in CommentReport.Reason.values:
        messages.error(request, 'Invalid report reason.')
        return redirect(redirect_url)

    report, created = CommentReport.objects.get_or_create(
        comment=comment,
        reported_by=request.user,
        defaults={'reason': reason, 'notes': notes},
    )

    if created:
        # Put the comment back into moderation
        comment.status = Comment.STATUS_PENDING
        comment.save(update_fields=['status', 'updated_at'])
        messages.success(
            request, 'Thanks for the report. The moderation team has been notified.')
    else:
        messages.info(request, 'You already reported this comment.')

    return redirect(redirect_url)


@login_required
@require_POST
def delete_comment(request, pk):
    """Allow comment authors or staff to delete a comment."""
    comment = get_object_or_404(Comment, pk=pk)
    redirect_url = request.POST.get('next') or comment.post.get_absolute_url()

    if not (request.user.is_staff or request.user == comment.author):
        return HttpResponseForbidden('You cannot delete this comment.')

    comment.delete()
    messages.success(request, 'Comment deleted.')
    return redirect(redirect_url)
