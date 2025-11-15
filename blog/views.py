# /* ============================================================
#    *** BLOG: Views ***
#    ============================================================ */
"""Define blog view logic."""

# /* ============================================================
#    *** BLOG: Views: Imports ***
#    ============================================================ */
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from accounts.utils import ensure_verified_email, verified_email_required

from .forms import BlogPostForm, PublicBlogPostForm, CommentForm
from .models import (
    BlogPost,
    Comment,
    CommentReaction,
    CommentReport,
    PostReaction,
    ReactionType,
)

# /* ============================================================
#    *** BLOG: Views: Reaction Constants ***
#    ============================================================ */

REACTION_ICON_MAP = {
    ReactionType.LIKE.value: "fa-thumbs-up",
    ReactionType.LOVE.value: "fa-heart",
    ReactionType.DISLIKE.value: "fa-thumbs-down",
}

# Options for rendering the reaction choices
REACTION_OPTIONS = [
    {
        "value": choice.value,
        "label": choice.label,
        "icon": REACTION_ICON_MAP[choice.value],
    }
    for choice in ReactionType
]

REACTION_VALUES = {opt["value"] for opt in REACTION_OPTIONS}

DEFAULT_BLOG_INDEX_PAGE_SIZE = 9


# /* ============================================================
#    *** BLOG: Views: Post Creation ***
#    ============================================================ */
@login_required
@verified_email_required
def new_post(request):
    """Handle creation of a new blog post."""
    if request.method == "POST":
        form = PublicBlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            action = request.POST.get("action") or "publish"
            post = form.save(commit=False)
            post.author = request.user

            if action == "save_draft":
                post.status = BlogPost.STATUS_DRAFT
                messages.success(
                    request,
                    "Draft saved — visible only to you.",
                )
                post.save()
                return redirect("blog:edit_post", pk=post.pk)

            if request.user.is_staff or request.user.is_superuser:
                post.status = BlogPost.STATUS_APPROVED
                messages.success(
                    request,
                    "Live now — your post is published.",
                )
            else:
                post.status = BlogPost.STATUS_PENDING
                messages.info(
                    request,
                    "Thanks! Your post is awaiting a quick review.",
                )

            post.save()
            return redirect("blog:index")
    else:
        form = PublicBlogPostForm()

    return render(request, "blog/new_post.html", {"form": form})


# /* ============================================================
#    *** BLOG: Views: Post Browsing ***
#    ============================================================ */

# pylint: disable=too-many-locals
def post_list(request, tag_slug=None):
    """Display approved posts with optional filtering."""
    search_query = (request.GET.get("q") or "").strip()
    raw_tag = (tag_slug or request.GET.get("tag") or "").strip()
    active_tag_slug = slugify(raw_tag) if raw_tag else ""

    posts_qs = (
        BlogPost.approved.select_related("author")
        .order_by("-published_at", "-updated_at")
    )

    if search_query:
        posts_qs = posts_qs.filter(
            Q(title__icontains=search_query)
            | Q(excerpt__icontains=search_query)
            | Q(body__icontains=search_query)
            | Q(tags__icontains=search_query)
        )

    posts = list(posts_qs)

    active_tag_label = raw_tag if raw_tag else ""
    if active_tag_slug:
        filtered_posts = []
        for post in posts:
            for tag in post.tag_list:
                if tag["slug"] == active_tag_slug:
                    filtered_posts.append(post)
                    # Prefer canonical casing from stored tag
                    active_tag_label = tag["name"]
                    break
        posts = filtered_posts

    page_size = getattr(
        settings, "BLOG_INDEX_PAGE_SIZE", DEFAULT_BLOG_INDEX_PAGE_SIZE
    )
    paginator = Paginator(posts, page_size)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    preserved_querydict = request.GET.copy()
    preserved_querydict.pop("page", None)
    paginator_querystring = preserved_querydict.urlencode()

    context = {
        "posts": page_obj.object_list,
        "page_obj": page_obj,
        "search_query": search_query,
        "active_tag_slug": active_tag_slug,
        "active_tag_label": active_tag_label,
        "paginator_querystring": paginator_querystring,
    }
    return render(request, "blog/index.html", context)


# pylint: disable=too-many-locals, too-many-branches, too-many-statements
def post_detail(request, year, month, day, slug):
    """Display a single post with access control."""
    qs = BlogPost.objects.filter(slug=slug).filter(
        Q(
            published_at__year=year,
            published_at__month=month,
            published_at__day=day,
        )
        | Q(
            published_at__isnull=True,
            created_at__year=year,
            created_at__month=month,
            created_at__day=day,
        )
    )
    post = get_object_or_404(qs)

    if (
        post.status != BlogPost.STATUS_APPROVED
        and not (
            request.user.is_authenticated
            and (
                request.user == post.author
                or request.user.is_staff
                or request.user.is_superuser
            )
        )
    ):
        return HttpResponse("Not found", status=404)

    is_draft = post.status == BlogPost.STATUS_DRAFT
    show_engagement = not is_draft

    comment_form = None
    approved_comments = []
    post_reaction_display = []

    if show_engagement:
        comment_form = CommentForm()

        if request.method == "POST":
            # New comment submission
            comment_form = CommentForm(request.POST)
            if not request.user.is_authenticated:
                messages.error(
                    request,
                    "Please sign in to join the conversation.",
                )
            else:
                redirect_response = ensure_verified_email(request)
                if redirect_response is not None:
                    return redirect_response

            if request.user.is_authenticated and comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.post = post
                comment.author = request.user
                if request.user.is_staff or request.user.is_superuser:
                    comment.status = Comment.STATUS_APPROVED
                    comment.save()
                    messages.success(
                        request, "Live now — your staff comment is visible.")
                else:
                    comment.status = Comment.STATUS_PENDING
                    comment.save()
                    messages.success(
                        request, "Thanks! Your comment is awaiting a quick review."
                    )
                return redirect(post.get_absolute_url())

            messages.error(request, "Oops — we couldn’t accept that comment.")

        # Comments (approved only for public)
        approved_comments = list(
            post.comments.approved()
            .select_related("author")
            .prefetch_related("reactions__user", "reports__reported_by")
        )

        # Post reactions
        post_reactions = list(post.reactions.select_related("user"))
        post_reaction_totals = {opt["value"]: 0 for opt in REACTION_OPTIONS}
        for reaction in post_reactions:
            post_reaction_totals[reaction.reaction] = (
                post_reaction_totals.get(reaction.reaction, 0) + 1
            )

        user_post_reaction = None
        if request.user.is_authenticated:
            for reaction in post_reactions:
                if reaction.user_id == request.user.id:
                    user_post_reaction = reaction.reaction
                    break

        post_reaction_display = [
            {
                **opt,
                "count": post_reaction_totals.get(opt["value"], 0),
                "active": opt["value"] == user_post_reaction,
            }
            for opt in REACTION_OPTIONS
        ]

    # Permissions for UI actions on the post
    if request.user.is_authenticated:
        post.can_edit = request.user == post.author
        post.can_delete = (
            request.user == post.author
            or request.user.is_staff
            or request.user.is_superuser
        )
    else:
        post.can_edit = False
        post.can_delete = False

    # Comment reactions + permissions
    for comment in approved_comments:
        totals = {opt["value"]: 0 for opt in REACTION_OPTIONS}
        user_comment_reaction = None

        for reaction in comment.reactions.all():
            totals[reaction.reaction] = totals.get(reaction.reaction, 0) + 1
            if (
                request.user.is_authenticated
                and reaction.user_id == request.user.id
            ):
                user_comment_reaction = reaction.reaction

        comment.reaction_display = [
            {
                **opt,
                "count": totals.get(opt["value"], 0),
                "active": opt["value"] == user_comment_reaction,
            }
            for opt in REACTION_OPTIONS
        ]

        comment.can_delete = False
        comment.can_report = False
        comment.user_reported = False
        comment.can_edit = False
        if request.user.is_authenticated:
            comment.can_delete = (
                request.user.is_staff
                or request.user.is_superuser
                or request.user == comment.author
            )
            comment.can_edit = request.user == comment.author
            can_report = (not request.user.is_staff) and (
                request.user != comment.author
            )
            comment.can_report = can_report
            if can_report:
                for rep in comment.reports.all():
                    if rep.reported_by_id == request.user.id:
                        comment.user_reported = True
                        break

    context = {
        "post": post,
        "comments": approved_comments,
        "comment_form": comment_form,
        "post_reaction_display": post_reaction_display,
        "show_engagement": show_engagement,
        "is_draft": is_draft,
    }
    return render(request, "blog/post_detail.html", context)


# /* ============================================================
#    *** BLOG: Views: Post Management ***
#    ============================================================ */
@login_required
# pylint: disable=too-many-branches, too-many-statements
def edit_post(request, pk):
    """Handle editing of an existing post."""
    post = get_object_or_404(BlogPost, pk=pk)

    if post.author != request.user:
        raise PermissionDenied("You cannot edit this post.")

    redirect_url = (
        request.POST.get("next")
        or request.GET.get("next")
        or post.get_absolute_url()
    )

    # Staff/superuser can use full form; regular users limited form
    form_class = (
        BlogPostForm
        if (request.user.is_staff or request.user.is_superuser)
        else PublicBlogPostForm
    )

    hide_author_field = (
        post.status == BlogPost.STATUS_DRAFT
        and (request.user.is_staff or request.user.is_superuser)
    )

    if request.method == "POST":
        form = form_class(request.POST, request.FILES, instance=post)
        original_status = post.status
        original_featured = getattr(post, "featured", False)
        if isinstance(form, BlogPostForm):
            if hide_author_field:
                form.fields.pop("author", None)
            elif "author" in form.fields:
                form.fields["author"].disabled = True

        if form.is_valid():
            updated_post = form.save(commit=False)
            updated_post.author = post.author
            action = request.POST.get("action") or "save"
            message_text = "All set! Your post was updated."
            message_level = messages.success
            if request.user.is_staff or request.user.is_superuser:
                if action == "save_draft":
                    updated_post.status = BlogPost.STATUS_DRAFT
                    message_text = "Draft saved — visible only to you."
                elif action == "publish":
                    updated_post.status = BlogPost.STATUS_APPROVED
                    message_text = "Live now — your post is published."
            else:
                if action == "save_draft":
                    updated_post.status = BlogPost.STATUS_DRAFT
                    message_text = "Draft updated."
                elif action == "publish":
                    if original_status == BlogPost.STATUS_APPROVED:
                        updated_post.status = BlogPost.STATUS_APPROVED
                        message_text = "All set! Your post was updated."
                    else:
                        updated_post.status = BlogPost.STATUS_PENDING
                        message_text = "Thanks! Your post is awaiting a quick review."
                        message_level = messages.info
                else:
                    updated_post.status = original_status
                    if original_status == BlogPost.STATUS_DRAFT:
                        message_text = "Draft updated."
                    elif original_status == BlogPost.STATUS_PENDING:
                        message_text = "Post updated — still awaiting review."
                        message_level = messages.info

                if hasattr(updated_post, "featured"):
                    updated_post.featured = original_featured

            updated_post.save()
            message_level(request, message_text)
            return redirect(redirect_url)
    else:
        form = form_class(instance=post)
        if isinstance(form, BlogPostForm):
            if hide_author_field:
                form.fields.pop("author", None)
            elif "author" in form.fields:
                form.fields["author"].disabled = True

    return render(
        request,
        "blog/edit_post.html",
        {
            "form": form,
            "post": post,
            "next_url": redirect_url,
            "hide_author_field": hide_author_field,
        },
    )


# /* ============================================================
#    *** BLOG: Views: Comment Management ***
#    ============================================================ */
@login_required
def edit_comment(request, pk):
    """Handle editing of an existing comment."""
    comment = get_object_or_404(Comment, pk=pk)

    if comment.author != request.user:
        raise PermissionDenied("You cannot edit this comment.")

    redirect_url = (
        request.POST.get("next")
        or request.GET.get("next")
        or f"{comment.post.get_absolute_url()}#comment-{comment.pk}"
    )

    if request.method == "POST":
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            comment.body = form.cleaned_data["body"]
            comment.save(update_fields=["body", "updated_at"])
            messages.success(request, "All set! Your comment was updated.")
            return redirect(redirect_url)
    else:
        form = CommentForm(instance=comment)

    return render(
        request,
        "blog/edit_comment.html",
        {"form": form, "comment": comment, "next_url": redirect_url},
    )


# /* ============================================================
#    *** BLOG: Views: Reaction Handling ***
#    ============================================================ */
@login_required
@verified_email_required
@require_POST
def react_to_post(request, pk):
    """Manage a user's reaction on a post."""
    post = get_object_or_404(BlogPost, pk=pk)
    reaction_value = request.POST.get("reaction")
    redirect_url = request.POST.get("next") or post.get_absolute_url()

    if reaction_value not in REACTION_VALUES:
        messages.error(request, "Oops — that reaction isn’t valid.")
        return redirect(redirect_url)

    reaction, created = PostReaction.objects.get_or_create(
        post=post, user=request.user
    )

    # Toggle: if same reaction posted again, remove it
    if not created and reaction.reaction == reaction_value:
        reaction.delete()
        messages.info(request, "Reaction removed.")
    else:
        reaction.reaction = reaction_value
        reaction.save(update_fields=["reaction", "updated_at"])
        messages.success(request, "Reaction saved!")

    return redirect(redirect_url)


@login_required
@verified_email_required
@require_POST
def react_to_comment(request, pk):
    """Manage a user's reaction on a comment."""
    comment = get_object_or_404(Comment, pk=pk)
    redirect_url = (
        request.POST.get("next")
        or f"{comment.post.get_absolute_url()}#comment-{comment.pk}"
    )

    # Only staff can react to non-approved comments
    if comment.status != Comment.STATUS_APPROVED and not request.user.is_staff:
        messages.error(request, "You can’t react to a non-approved comment.")
        return redirect(redirect_url)

    reaction_value = request.POST.get("reaction")
    if reaction_value not in REACTION_VALUES:
        messages.error(request, "Oops — that reaction isn’t valid.")
        return redirect(redirect_url)

    reaction, created = CommentReaction.objects.get_or_create(
        comment=comment, user=request.user
    )

    # Toggle: if same reaction posted again, remove it
    if not created and reaction.reaction == reaction_value:
        reaction.delete()
        messages.info(request, "Comment reaction removed.")
    else:
        reaction.reaction = reaction_value
        reaction.save(update_fields=["reaction", "updated_at"])
        messages.success(request, "Comment reaction saved!")

    return redirect(redirect_url)


# /* ============================================================
#    *** BLOG: Views: Comment Moderation ***
#    ============================================================ */
@login_required
@require_POST
def report_comment(request, pk):
    """Handle user reports against a comment."""
    comment = get_object_or_404(Comment, pk=pk)
    redirect_url = (
        request.POST.get("next")
        or f"{comment.post.get_absolute_url()}#comment-{comment.pk}"
    )

    if request.user.is_staff or request.user.is_superuser:
        raise PermissionDenied("Staff members cannot report comments.")

    if comment.author_id == request.user.id:
        messages.error(request, "You can’t report your own comment.")
        return redirect(redirect_url)

    reason = request.POST.get("reason")
    notes = (request.POST.get("notes") or "").strip()

    if reason not in CommentReport.Reason.values:
        messages.error(request, "Pick a valid reason to report.")
        return redirect(redirect_url)

    _report, created = CommentReport.objects.get_or_create(
        comment=comment,
        reported_by=request.user,
        defaults={'reason': reason, 'notes': notes},
    )

    if created:
        # Put the comment back into moderation
        comment.status = Comment.STATUS_PENDING
        comment.save(update_fields=["status", "updated_at"])
        messages.success(
            request,
            "Thanks for flagging this — our moderators have been notified.",
        )
    else:
        messages.info(request, "You’ve already reported this comment.")

    return redirect(redirect_url)


@login_required
@require_POST
def delete_comment(request, pk):
    """Delete a comment when permitted."""
    comment = get_object_or_404(Comment, pk=pk)
    redirect_url = request.POST.get("next") or comment.post.get_absolute_url()

    if not (
        request.user.is_staff
        or request.user.is_superuser
        or request.user == comment.author
    ):
        raise PermissionDenied("You cannot delete this comment.")

    comment.delete()
    messages.success(request, "Comment removed.")
    return redirect(redirect_url)


@login_required
@require_POST
def delete_post(request, pk):
    """Delete a post when permitted."""
    post = get_object_or_404(BlogPost, pk=pk)

    if not (
        request.user == post.author
        or request.user.is_staff
        or request.user.is_superuser
    ):
        raise PermissionDenied("You cannot delete this post.")

    post.delete()
    messages.success(request, "Post removed.")
    return redirect("blog:index")
