# ============================================================
# *** ACCOUNTS VIEWS: Controllers and staff tools ***
# ============================================================

from allauth.account.models import EmailAddress
from allauth.account.views import PasswordChangeView
from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.formats import date_format

from blog.models import BlogPost, Comment, CommentReport, log_moderation_action
from pages.models import HelpRequest
from .forms import ProfileForm
from .models import UserProfile
from .utils import ensure_verified_email, verified_email_required

User = get_user_model()


# -----------------------------------------------------------
# Helpers
# -----------------------------------------------------------

def _get_profile(user):
    """Fetch or create the user's profile."""
    user_profile, _ = UserProfile.objects.get_or_create(user=user)
    return user_profile


def _process_email_change(request, user, new_email):
    """Upsert EmailAddress, reset verification, and send confirmation."""
    normalized = new_email.strip().lower() if new_email else ""
    if not normalized:
        EmailAddress.objects.filter(user=user).delete()
        return

    EmailAddress.objects.filter(user=user).exclude(
        email__iexact=normalized
    ).delete()

    email_record = (
        EmailAddress.objects.filter(
            user=user, email__iexact=normalized).first()
        or EmailAddress(user=user)
    )

    changed = []
    if email_record.email != normalized:
        email_record.email = normalized
        changed.append("email")
    if not email_record.primary:
        email_record.primary = True
        changed.append("primary")
    if email_record.verified:
        email_record.verified = False
        changed.append("verified")

    if email_record.pk is None:
        email_record.save()
    elif changed:
        email_record.save(update_fields=changed)

    email_record.send_confirmation(request=request)
    messages.info(
        request,
        "Confirmation sent — check your inbox to verify the new address.",
    )


def _compute_last_active(user, posts, comments, drafts, is_self):
    """Compute a best-effort 'last active' timestamp."""
    candidates = []
    if user.last_login:
        candidates.append(user.last_login)
    latest_post = posts.first()
    if latest_post:
        candidates.append(latest_post.published_at or latest_post.created_at)
    latest_comment = comments.first()
    if latest_comment:
        candidates.append(latest_comment.created_at)
    if is_self and drafts:
        candidates.append(drafts[0].updated_at)
    return max(candidates) if candidates else None


def _build_staff_tools():
    """Build staff tool cards with counters."""
    return [
        {
            "label": "Pending posts",
            "url": reverse("accounts:staff_pending_posts"),
            "icon": "fa-newspaper",
            "count": BlogPost.objects.filter(status=BlogPost.STATUS_PENDING).count(),
        },
        {
            "label": "Pending comments",
            "url": reverse("accounts:staff_pending_comments"),
            "icon": "fa-comments",
            "count": Comment.objects.filter(status=Comment.STATUS_PENDING).count(),
        },
        {
            "label": "Reports",
            "url": reverse("accounts:staff_reports"),
            "icon": "fa-triangle-exclamation",
            "count": CommentReport.objects.filter(resolved=False).count(),
        },
        {
            "label": "Help requests",
            "url": reverse("accounts:staff_help_requests"),
            "icon": "fa-life-ring",
            "count": HelpRequest.objects.exclude(
                status=HelpRequest.STATUS_RESOLVED
            ).count(),
        },
    ]


# -----------------------------------------------------------
# Public and profile views
# -----------------------------------------------------------

def profile(request, username):
    """Show a user's public profile page or CTA for unauthenticated viewers."""
    profile_user = get_object_or_404(
        User.objects.select_related("profile"), username=username
    )
    if not request.user.is_authenticated:
        return render(
            request,
            "accounts/profile_cta.html",
            {
                "login_url": reverse("account_login"),
                "signup_url": reverse("account_signup"),
            },
        )

    is_self = request.user.pk == profile_user.pk
    profile_obj = _get_profile(profile_user)

    approved_posts = (
        profile_user.blog_posts.filter(status=BlogPost.STATUS_APPROVED)
        .select_related("author")
        .order_by("-published_at", "-created_at")
    )
    approved_comments = (
        profile_user.comments.filter(status=Comment.STATUS_APPROVED)
        .select_related("post", "post__author", "author")
        .order_by("-created_at")
    )

    draft_posts = (
        list(
            profile_user.blog_posts.filter(status=BlogPost.STATUS_DRAFT)
            .select_related("author")
            .order_by("-updated_at")
        )
        if is_self
        else []
    )

    posts_page = (
        Paginator(approved_posts, 5).get_page(request.GET.get("post_page"))
        if is_self
        else None
    )
    comments_page = (
        Paginator(approved_comments, 5).get_page(
            request.GET.get("comment_page"))
        if is_self
        else None
    )

    role_badge = None
    if profile_user.is_superuser:
        role_badge = {"label": "Admin", "css_class": "comp-badge--superadmin"}
    elif profile_user.is_staff:
        role_badge = {"label": "Staff", "css_class": "comp-badge--staff"}

    has_favorites = bool(
        (profile_obj.favorite_games or "").strip()
        or (profile_obj.favorite_genres or "").strip()
    )

    dob_display = None
    if profile_obj.date_of_birth:
        dob_format = "F j, Y" if is_self else "F j"
        dob_display = date_format(profile_obj.date_of_birth, dob_format)

    context = {
        "profile_user": profile_user,
        "profile": profile_obj,
        "is_self": is_self,
        "public_only": not is_self,
        "role_badge": role_badge,
        "member_since": profile_user.date_joined,
        "last_active": _compute_last_active(
            profile_user, approved_posts, approved_comments, draft_posts, is_self
        ),
        "stats": {
            "public_posts": approved_posts.count(),
            "approved_comments": approved_comments.count(),
        },
        "has_favorites": has_favorites,
        "date_of_birth_display": dob_display,
        "full_name": (profile_user.get_full_name() or "").strip() if is_self else None,
        "draft_posts": draft_posts,
        "posts_page": posts_page,
        "comments_page": comments_page,
        "show_moderation_tools": is_self and profile_user.is_staff,
        "staff_tools": _build_staff_tools() if (is_self and profile_user.is_staff) else [],
    }
    return render(request, "accounts/profile.html", context)


@login_required
def profile_edit(request):
    """Update profile and email, then redirect to the profile page."""
    profile_obj = _get_profile(request.user)
    if request.method == "POST":
        form = ProfileForm(
            request.POST, request.FILES, instance=profile_obj, user=request.user
        )
        if form.is_valid():
            form.save()
            if getattr(form, "email_changed", False):
                _process_email_change(request, request.user, form.new_email)
            messages.success(request, "All set! Your profile was updated.")
            return redirect("accounts:profile", request.user.username)
    else:
        form = ProfileForm(instance=profile_obj, user=request.user)

    return render(request, "accounts/profile_edit.html", {"form": form})


@login_required
@verified_email_required
def profile_delete(request):
    """Delete the current user's account after password confirmation."""
    if request.method == "POST":
        password = (request.POST.get("confirm_password") or "").strip()
        if not request.user.check_password(password):
            messages.error(
                request, "Incorrect password — account not deleted.")
            return redirect("accounts:profile_delete")

        user = request.user
        logout(request)
        username = user.username
        user.delete()
        messages.success(
            request, f"Your account '{username}' has been deleted.")
        return redirect("pages:home")

    return render(request, "accounts/profile_delete.html")


@login_required
def my_profile_redirect(request):
    """Redirect the logged in user to their own profile page."""
    return redirect("accounts:profile", request.user.username)


class VerifiedEmailPasswordChangeView(PasswordChangeView):
    """Password change view that requires a verified email."""

    def dispatch(self, request, *args, **kwargs):
        response = ensure_verified_email(request)
        if response is not None:
            return response
        return super().dispatch(request, *args, **kwargs)


# -----------------------------------------------------------
# Staff tools
# -----------------------------------------------------------

@staff_member_required
def staff_dashboard(request):
    """Staff overview with counters and quick links to moderation tasks."""
    counters = {
        "pending_posts": BlogPost.objects.filter(status=BlogPost.STATUS_PENDING).count(),
        "pending_comments": Comment.objects.filter(status=Comment.STATUS_PENDING).count(),
        "unresolved_reports": CommentReport.objects.filter(resolved=False).count(),
        "open_help_requests": HelpRequest.objects.exclude(
            status=HelpRequest.STATUS_RESOLVED
        ).count(),
        "featured_posts": BlogPost.objects.filter(featured=True).count(),
        "total_users": User.objects.count(),
    }
    quick_links = [
        {
            "label": "Pending posts",
            "url": reverse("accounts:staff_pending_posts"),
            "icon": "fa-newspaper",
        },
        {
            "label": "Pending comments",
            "url": reverse("accounts:staff_pending_comments"),
            "icon": "fa-comments",
        },
        {
            "label": "Reports",
            "url": reverse("accounts:staff_reports"),
            "icon": "fa-triangle-exclamation",
        },
        {
            "label": "Help requests",
            "url": reverse("accounts:staff_help_requests"),
            "icon": "fa-life-ring",
        },
        {
            "label": "User search",
            "url": reverse("accounts:staff_user_search"),
            "icon": "fa-users",
        },
        {
            "label": "Featured manager",
            "url": reverse("accounts:staff_featured_manager"),
            "icon": "fa-star",
        },
        {
            "label": "Content search",
            "url": reverse("accounts:staff_content_search"),
            "icon": "fa-search",
        },
        {"label": "Admin", "url": reverse(
            "admin:index"), "icon": "fa-gauge-high"},
    ]
    return render(
        request,
        "accounts/staff/dashboard.html",
        {"counters": counters, "quick_links": quick_links},
    )


@staff_member_required
def staff_pending_posts(request):
    """Moderate pending posts with approve, reject, or delete actions."""
    if request.method == "POST":
        post_id = request.POST.get("post_id")
        action = request.POST.get("action") or ""
        post = get_object_or_404(
            BlogPost.objects.select_related("author"), pk=post_id
        )
        if action == "approve":
            post.status = BlogPost.STATUS_APPROVED
            post.save()
            log_moderation_action(request.user, "approve_post", post)
            messages.success(
                request, f"Approved — '{post.title}' is now live.")
        elif action == "reject":
            post.status = BlogPost.STATUS_REJECTED
            post.save()
            log_moderation_action(request.user, "reject_post", post)
            messages.info(request, f"Rejected — '{post.title}' is hidden.")
        elif action == "delete":
            log_moderation_action(request.user, "delete_post", post)
            post.delete()
            messages.warning(request, "Deleted — the post was removed.")
        else:
            messages.error(request, "Oops — unknown action.")
        return redirect("accounts:staff_pending_posts")

    qs = BlogPost.objects.filter(
        status=BlogPost.STATUS_PENDING
    ).select_related("author")
    paginator = Paginator(qs.order_by("created_at"), 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "accounts/staff/pending_posts.html",
        {"page_obj": page_obj, "total_pending": qs.count()},
    )


@staff_member_required
def staff_pending_comments(request):
    """Moderate pending comments with approve, reject, or delete actions."""
    if request.method == "POST":
        comment_id = request.POST.get("comment_id")
        action = request.POST.get("action") or ""
        comment = get_object_or_404(
            Comment.objects.select_related("author", "post"), pk=comment_id
        )
        if action == "approve":
            comment.status = Comment.STATUS_APPROVED
            comment.save()
            log_moderation_action(request.user, "approve_comment", comment)
            messages.success(request, "Approved — the comment is now visible.")
        elif action == "reject":
            comment.status = Comment.STATUS_REJECTED
            comment.save()
            log_moderation_action(request.user, "reject_comment", comment)
            messages.info(request, "Rejected — the comment is hidden.")
        elif action == "delete":
            log_moderation_action(request.user, "delete_comment", comment)
            comment.delete()
            messages.warning(request, "Deleted — the comment was removed.")
        else:
            messages.error(request, "Oops — unknown action.")
        return redirect("accounts:staff_pending_comments")

    qs = Comment.objects.filter(status=Comment.STATUS_PENDING).select_related(
        "author", "post", "post__author"
    )
    paginator = Paginator(qs.order_by("created_at"), 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "accounts/staff/pending_comments.html",
        {"page_obj": page_obj, "total_pending": qs.count()},
    )


@staff_member_required
def staff_reports(request):
    """Handle comment reports by resolving, rejecting, or deleting comments."""
    if request.method == "POST":
        report_id = request.POST.get("report_id")
        action = request.POST.get("action") or ""
        report = get_object_or_404(
            CommentReport.objects.select_related("comment", "comment__post"),
            pk=report_id,
        )
        comment = report.comment
        if action == "resolve":
            report.resolved = True
            report.save(update_fields=["resolved"])
            log_moderation_action(
                request.user, "resolve_report", comment, notes=f"Report #{report.pk} resolved"
            )
            messages.success(request, "Resolved — the report has been closed.")
        elif action == "reject_comment":
            if comment:
                comment.status = Comment.STATUS_REJECTED
                comment.save()
                log_moderation_action(
                    request.user, "reject_comment", comment, notes=f"Report #{report.pk} rejected"
                )
            report.resolved = True
            report.save(update_fields=["resolved"])
            messages.info(
                request, "Rejected — comment hidden and report closed.")
        elif action == "delete_comment" and comment:
            log_moderation_action(
                request.user, "delete_comment", comment, notes=f"Report #{report.pk}"
            )
            comment.delete()
            report.resolved = True
            report.save(update_fields=["resolved"])
            messages.warning(
                request, "Deleted — comment removed and report closed.")
        else:
            messages.error(request, "Oops — unknown action.")
        return redirect("accounts:staff_reports")

    qs = CommentReport.objects.filter(resolved=False).select_related(
        "comment", "comment__author", "comment__post"
    )
    paginator = Paginator(qs.order_by("-created_at"), 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "accounts/staff/reports.html",
        {"page_obj": page_obj, "total_reports": qs.count()},
    )


@staff_member_required
def staff_help_requests(request):
    """Track and update help requests with resolve or progress actions."""
    if request.method == "POST":
        req_id = request.POST.get("request_id")
        action = request.POST.get("action") or ""
        help_request = get_object_or_404(HelpRequest, pk=req_id)
        if action == "resolve":
            help_request.status = HelpRequest.STATUS_RESOLVED
            help_request.save(update_fields=["status", "updated_at"])
            messages.success(request, "Resolved — help request closed.")
        elif action == "progress":
            help_request.status = HelpRequest.STATUS_IN_PROGRESS
            help_request.save(update_fields=["status", "updated_at"])
            messages.info(request, "In progress — help request updated.")
        else:
            messages.error(request, "Oops — unknown action.")
        return redirect("accounts:staff_help_requests")

    qs = HelpRequest.objects.exclude(status=HelpRequest.STATUS_RESOLVED)
    paginator = Paginator(qs.order_by("-created_at"), 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "accounts/staff/help_requests.html",
        {"page_obj": page_obj, "open_count": qs.count()},
    )


@staff_member_required
def staff_user_search(request):
    """Search users by username or email and list results."""
    query = (request.GET.get("q") or "").strip()
    results = User.objects.none()
    if query:
        results = (
            User.objects.select_related("profile")
            .filter(Q(username__icontains=query) | Q(email__icontains=query))
            .order_by("username")
        )
    paginator = Paginator(results, 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "accounts/staff/user_search.html",
        {"page_obj": page_obj, "query": query},
    )


@staff_member_required
def staff_featured_manager(request):
    """Toggle featured flag on posts and browse featured content."""
    if request.method == "POST":
        post_id = request.POST.get("post_id")
        action = request.POST.get("action") or ""
        post = get_object_or_404(
            BlogPost.objects.select_related("author"), pk=post_id
        )
        if action == "feature":
            post.featured = True
            post.save(update_fields=["featured", "updated_at"])
            log_moderation_action(request.user, "feature_post", post)
            messages.success(
                request, f"Featured — '{post.title}' is now spotlighted.")
        elif action == "unfeature":
            post.featured = False
            post.save(update_fields=["featured", "updated_at"])
            log_moderation_action(request.user, "unfeature_post", post)
            messages.info(
                request, f"Unfeatured — '{post.title}' removed from spotlight.")
        else:
            messages.error(request, "Oops — unknown action.")
        return redirect("accounts:staff_featured_manager")

    qs = BlogPost.objects.select_related("author").order_by(
        models.F("featured").desc(), "-published_at", "-updated_at"
    )
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "accounts/staff/featured_manager.html",
        {
            "page_obj": page_obj,
            "featured_total": BlogPost.objects.filter(featured=True).count(),
        },
    )


@staff_member_required
def staff_content_search(request):
    """Search posts and comments by a free text query and return recent matches."""
    query = (request.GET.get("q") or "").strip()
    posts, comments = [], []
    if query:
        posts = list(
            BlogPost.objects.select_related("author")
            .filter(
                Q(title__icontains=query)
                | Q(body__icontains=query)
                | Q(tags__icontains=query)
            )
            .order_by("-published_at", "-updated_at")[:25]
        )
        comments = list(
            Comment.objects.select_related("author", "post")
            .filter(body__icontains=query)
            .order_by("-created_at")[:25]
        )
    return render(
        request,
        "accounts/staff/content_search.html",
        {"query": query, "posts": posts, "comments": comments},
    )


@staff_member_required
def staff_view_as_user(request):
    """Preview a user's public profile to assist moderation decisions."""
    username = (request.GET.get("username") or "").strip()
    preview_user, preview_profile = None, None
    preview_posts, preview_comments, preview_stats, last_active = [], [], {}, None

    if username:
        preview_user = get_object_or_404(
            User.objects.select_related("profile"), username=username
        )
        preview_profile = _get_profile(preview_user)

        posts_qs = (
            preview_user.blog_posts.filter(status=BlogPost.STATUS_APPROVED)
            .select_related("author")
            .order_by("-published_at", "-created_at")
        )
        comments_qs = (
            preview_user.comments.filter(status=Comment.STATUS_APPROVED)
            .select_related("post", "post__author", "author")
            .order_by("-created_at")
        )

        preview_posts = list(posts_qs[:5])
        preview_comments = list(comments_qs[:5])
        preview_stats = {
            "public_posts": posts_qs.count(),
            "approved_comments": comments_qs.count(),
        }

        candidates = []
        if preview_user.last_login:
            candidates.append(preview_user.last_login)
        if preview_posts:
            candidates.append(
                preview_posts[0].published_at or preview_posts[0].created_at)
        if preview_comments:
            candidates.append(preview_comments[0].created_at)
        if candidates:
            last_active = max(candidates)

    context = {
        "username": username,
        "preview_user": preview_user,
        "preview_profile": preview_profile,
        "preview_posts": preview_posts,
        "preview_comments": preview_comments,
        "preview_stats": preview_stats,
        "last_active": last_active,
    }
    return render(request, "accounts/staff/view_as_user.html", context)
