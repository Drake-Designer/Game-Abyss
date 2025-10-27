from datetime import datetime

from allauth.account.models import EmailAddress
from allauth.account.views import PasswordChangeView
from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from blog.models import BlogPost, Comment, CommentReport, log_moderation_action
from pages.models import HelpRequest
from .forms import ProfileForm
from .models import UserProfile
from .utils import ensure_verified_email, staff_member_required, verified_email_required

User = get_user_model()


def _get_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def _process_email_change(request, user, new_email: str):
    normalized_email = new_email or ""
    if not normalized_email:
        EmailAddress.objects.filter(user=user).delete()
        return

    EmailAddress.objects.filter(user=user).exclude(
        email__iexact=normalized_email).delete()

    email_qs = EmailAddress.objects.filter(
        user=user, email__iexact=normalized_email)
    email_address = email_qs.first() or EmailAddress(user=user)

    changed_fields: list[str] = []
    if email_address.email != normalized_email:
        email_address.email = normalized_email
        changed_fields.append("email")
    if not email_address.primary:
        email_address.primary = True
        changed_fields.append("primary")
    if email_address.verified:
        email_address.verified = False
        changed_fields.append("verified")

    if email_address.pk is None:
        email_address.save()
    elif changed_fields:
        email_address.save(update_fields=changed_fields)

    email_address.send_confirmation(request=request)
    messages.info(
        request, "We've sent a confirmation email. Please verify the new address to activate it.")


def profile(request, username):
    """Public profile page with activity and metadata."""
    profile_user = get_object_or_404(
        User.objects.select_related("profile"), username=username)
    profile_obj = _get_profile(profile_user)
    is_self = request.user.is_authenticated and request.user.pk == profile_user.pk

    approved_posts_qs = (
        profile_user.blog_posts.filter(status=BlogPost.STATUS_APPROVED)
        .select_related("author")
        .order_by("-published_at", "-created_at")
    )
    approved_comments_qs = (
        profile_user.comments.filter(status=Comment.STATUS_APPROVED)
        .select_related("post", "post__author", "author")
        .order_by("-created_at")
    )

    draft_posts = []
    if is_self:
        draft_posts = list(
            profile_user.blog_posts.filter(status=BlogPost.STATUS_DRAFT)
            .select_related("author")
            .order_by("-updated_at")
        )

    Paginator(approved_posts_qs, 5).get_page(request.GET.get("post_page"))
    Paginator(approved_comments_qs, 5).get_page(
        request.GET.get("comment_page"))

    public_post_count = approved_posts_qs.count()
    approved_comment_count = approved_comments_qs.count()

    full_name_value = (profile_user.get_full_name() or "").strip()

    role_badge: dict[str, str] | None = None
    if profile_user.is_superuser:
        role_badge = {"label": "Admin", "css_class": "comp-badge--admin"}
    elif profile_user.is_staff:
        role_badge = {"label": "Staff", "css_class": "comp-badge--staff"}

    last_active_candidates: list[datetime] = []
    if profile_user.last_login:
        last_active_candidates.append(profile_user.last_login)
    latest_post = approved_posts_qs.first()
    if latest_post:
        last_active_candidates.append(
            latest_post.published_at or latest_post.created_at)
    latest_comment = approved_comments_qs.first()
    if latest_comment:
        last_active_candidates.append(latest_comment.created_at)
    if draft_posts:
        last_active_candidates.append(draft_posts[0].updated_at)
    last_active = max(
        last_active_candidates) if last_active_candidates else None

    context = {
        "profile_user": profile_user,
        "profile": profile_obj,
        "is_self": is_self,
        "full_name": full_name_value if full_name_value else None,
        "approved_posts": list(approved_posts_qs),
        "approved_comments": list(approved_comments_qs),
        "public_post_count": public_post_count,
        "approved_comment_count": approved_comment_count,
        "role_badge": role_badge,
        "member_since": profile_user.date_joined,
        "last_active": last_active,
    }
    return render(request, "accounts/profile.html", context)


@login_required
def profile_edit(request):
    profile_obj = _get_profile(request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES,
                           instance=profile_obj, user=request.user)
        if form.is_valid():
            form.save()
            if form.email_changed:
                _process_email_change(request, request.user, form.new_email)
            messages.success(request, "Profile updated.")
            return redirect("accounts:profile", request.user.username)
    else:
        form = ProfileForm(instance=profile_obj, user=request.user)

    return render(request, "accounts/profile_edit.html", {"form": form})


@login_required
@verified_email_required
def profile_delete(request):
    if request.method == "POST":
        password = (request.POST.get("confirm_password") or "").strip()
        if not request.user.check_password(password):
            messages.error(
                request, "Incorrect password. Your account was not deleted.")
            return redirect("accounts:profile_delete")

        user = request.user
        logout(request)
        username = user.username
        user.delete()
        messages.success(request, f"Account {username} deleted.")
        return redirect("pages:home")

    return render(request, "accounts/profile_delete.html")


@login_required
def my_profile_redirect(request):
    return redirect("accounts:profile", request.user.username)


class VerifiedEmailPasswordChangeView(PasswordChangeView):
    def dispatch(self, request, *args, **kwargs):
        response = ensure_verified_email(request)
        if response is not None:
            return response
        return super().dispatch(request, *args, **kwargs)


@staff_member_required
def staff_dashboard(request):
    counters = {
        "pending_posts": BlogPost.objects.filter(status=BlogPost.STATUS_PENDING).count(),
        "pending_comments": Comment.objects.filter(status=Comment.STATUS_PENDING).count(),
        "unresolved_reports": CommentReport.objects.filter(resolved=False).count(),
        "open_help_requests": HelpRequest.objects.exclude(status=HelpRequest.STATUS_RESOLVED).count(),
        "featured_posts": BlogPost.objects.filter(featured=True).count(),
        "total_users": User.objects.count(),
    }
    quick_links = [
        {"label": "Pending posts", "url": reverse(
            "accounts:staff_pending_posts"), "icon": "fa-newspaper"},
        {"label": "Pending comments", "url": reverse(
            "accounts:staff_pending_comments"), "icon": "fa-comments"},
        {"label": "Reports", "url": reverse(
            "accounts:staff_reports"), "icon": "fa-triangle-exclamation"},
        {"label": "Help requests", "url": reverse(
            "accounts:staff_help_requests"), "icon": "fa-life-ring"},
        {"label": "User search", "url": reverse(
            "accounts:staff_user_search"), "icon": "fa-users"},
        {"label": "Featured manager", "url": reverse(
            "accounts:staff_featured_manager"), "icon": "fa-star"},
        {"label": "Content search", "url": reverse(
            "accounts:staff_content_search"), "icon": "fa-search"},
        {"label": "Admin", "url": reverse(
            "admin:index"), "icon": "fa-gauge-high"},
    ]
    return render(request, "accounts/staff/dashboard.html", {"counters": counters, "quick_links": quick_links})


@staff_member_required
def staff_pending_posts(request):
    if request.method == "POST":
        post_id = request.POST.get("post_id")
        action = request.POST.get("action") or ""
        post = get_object_or_404(
            BlogPost.objects.select_related("author"), pk=post_id)
        if action == "approve":
            post.status = BlogPost.STATUS_APPROVED
            post.save()
            log_moderation_action(request.user, "approve_post", post)
            messages.success(request, f"Approved '{post.title}'.")
        elif action == "reject":
            post.status = BlogPost.STATUS_REJECTED
            post.save()
            log_moderation_action(request.user, "reject_post", post)
            messages.info(request, f"Rejected '{post.title}'.")
        elif action == "delete":
            log_moderation_action(request.user, "delete_post", post)
            post.delete()
            messages.warning(request, "Post deleted.")
        else:
            messages.error(request, "Unknown action.")
        return redirect("accounts:staff_pending_posts")

    qs = BlogPost.objects.filter(
        status=BlogPost.STATUS_PENDING).select_related("author")
    paginator = Paginator(qs.order_by("created_at"), 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "accounts/staff/pending_posts.html", {"page_obj": page_obj, "total_pending": qs.count()})


@staff_member_required
def staff_pending_comments(request):
    if request.method == "POST":
        comment_id = request.POST.get("comment_id")
        action = request.POST.get("action") or ""
        comment = get_object_or_404(
            Comment.objects.select_related("author", "post"), pk=comment_id)
        if action == "approve":
            comment.status = Comment.STATUS_APPROVED
            comment.save()
            log_moderation_action(request.user, "approve_comment", comment)
            messages.success(request, "Comment approved.")
        elif action == "reject":
            comment.status = Comment.STATUS_REJECTED
            comment.save()
            log_moderation_action(request.user, "reject_comment", comment)
            messages.info(request, "Comment rejected.")
        elif action == "delete":
            log_moderation_action(request.user, "delete_comment", comment)
            comment.delete()
            messages.warning(request, "Comment deleted.")
        else:
            messages.error(request, "Unknown action.")
        return redirect("accounts:staff_pending_comments")

    qs = Comment.objects.filter(status=Comment.STATUS_PENDING).select_related(
        "author", "post", "post__author")
    paginator = Paginator(qs.order_by("created_at"), 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "accounts/staff/pending_comments.html", {"page_obj": page_obj, "total_pending": qs.count()})


@staff_member_required
def staff_reports(request):
    if request.method == "POST":
        report_id = request.POST.get("report_id")
        action = request.POST.get("action") or ""
        report = get_object_or_404(CommentReport.objects.select_related(
            "comment", "comment__post"), pk=report_id)
        comment = report.comment
        if action == "resolve":
            report.resolved = True
            report.save(update_fields=["resolved"])
            log_moderation_action(
                request.user, "resolve_report", comment, notes=f"Report #{report.pk} resolved")
            messages.success(request, "Report marked as resolved.")
        elif action == "reject_comment":
            if comment:
                comment.status = Comment.STATUS_REJECTED
                comment.save()
                log_moderation_action(
                    request.user, "reject_comment", comment, notes=f"Report #{report.pk} rejected")
            report.resolved = True
            report.save(update_fields=["resolved"])
            messages.info(request, "Comment rejected and report resolved.")
        elif action == "delete_comment" and comment:
            log_moderation_action(
                request.user, "delete_comment", comment, notes=f"Report #{report.pk}")
            comment.delete()
            report.resolved = True
            report.save(update_fields=["resolved"])
            messages.warning(request, "Comment deleted and report resolved.")
        else:
            messages.error(request, "Unknown action.")
        return redirect("accounts:staff_reports")

    qs = CommentReport.objects.filter(resolved=False).select_related(
        "comment", "comment__author", "comment__post")
    paginator = Paginator(qs.order_by("-created_at"), 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "accounts/staff/reports.html", {"page_obj": page_obj, "total_reports": qs.count()})


@staff_member_required
def staff_help_requests(request):
    if request.method == "POST":
        req_id = request.POST.get("request_id")
        action = request.POST.get("action") or ""
        help_request = get_object_or_404(HelpRequest, pk=req_id)
        if action == "resolve":
            help_request.status = HelpRequest.STATUS_RESOLVED
            help_request.save(update_fields=["status", "updated_at"])
            messages.success(request, "Help request resolved.")
        elif action == "progress":
            help_request.status = HelpRequest.STATUS_IN_PROGRESS
            help_request.save(update_fields=["status", "updated_at"])
            messages.info(request, "Help request marked in progress.")
        else:
            messages.error(request, "Unknown action.")
        return redirect("accounts:staff_help_requests")

    qs = HelpRequest.objects.exclude(status=HelpRequest.STATUS_RESOLVED)
    paginator = Paginator(qs.order_by("-created_at"), 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "accounts/staff/help_requests.html", {"page_obj": page_obj, "open_count": qs.count()})


@staff_member_required
def staff_user_search(request):
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
    return render(request, "accounts/staff/user_search.html", {"page_obj": page_obj, "query": query})


@staff_member_required
def staff_featured_manager(request):
    if request.method == "POST":
        post_id = request.POST.get("post_id")
        action = request.POST.get("action") or ""
        post = get_object_or_404(
            BlogPost.objects.select_related("author"), pk=post_id)
        if action == "feature":
            post.featured = True
            post.save(update_fields=["featured", "updated_at"])
            log_moderation_action(request.user, "feature_post", post)
            messages.success(request, f"Featured '{post.title}'.")
        elif action == "unfeature":
            post.featured = False
            post.save(update_fields=["featured", "updated_at"])
            log_moderation_action(request.user, "unfeature_post", post)
            messages.info(request, f"Removed '{post.title}' from featured.")
        else:
            messages.error(request, "Unknown action.")
        return redirect("accounts:staff_featured_manager")

    qs = BlogPost.objects.select_related("author").order_by(
        models.F("featured").desc(), "-published_at", "-updated_at")
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "accounts/staff/featured_manager.html",
        {"page_obj": page_obj, "featured_total": BlogPost.objects.filter(
            featured=True).count()},
    )


@staff_member_required
def staff_content_search(request):
    query = (request.GET.get("q") or "").strip()
    posts, comments = [], []
    if query:
        posts = list(
            BlogPost.objects.select_related("author")
            .filter(Q(title__icontains=query) | Q(body__icontains=query) | Q(tags__icontains=query))
            .order_by("-published_at", "-updated_at")[:25]
        )
        comments = list(
            Comment.objects.select_related("author", "post")
            .filter(body__icontains=query)
            .order_by("-created_at")[:25]
        )
    return render(request, "accounts/staff/content_search.html", {"query": query, "posts": posts, "comments": comments})


@staff_member_required
def staff_view_as_user(request):
    username = (request.GET.get("username") or "").strip()
    preview_user, preview_profile = None, None
    preview_posts, preview_comments, preview_stats, last_active = [], [], {}, None

    if username:
        preview_user = get_object_or_404(
            User.objects.select_related("profile"), username=username)
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

        last_active_candidates: list[datetime] = []
        if preview_user.last_login:
            last_active_candidates.append(preview_user.last_login)
        if preview_posts:
            last_active_candidates.append(
                preview_posts[0].published_at or preview_posts[0].created_at)
        if preview_comments:
            last_active_candidates.append(preview_comments[0].created_at)
        if last_active_candidates:
            last_active = max(last_active_candidates)

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
