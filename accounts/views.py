from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.decorators import login_required
from allauth.account.models import EmailAddress
from allauth.account.views import PasswordChangeView
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from blog.models import BlogPost, Comment, CommentReport

from .forms import ProfileForm
from .models import UserProfile
from .utils import ensure_verified_email, verified_email_required

User = get_user_model()


def _get_profile(user):
    """Return the user's profile, creating it if missing."""
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def _process_email_change(request, user, new_email: str):
    """Update EmailAddress records and trigger verification if needed."""
    normalized_email = new_email or ""

    if not normalized_email:
        EmailAddress.objects.filter(user=user).delete()
        return

    EmailAddress.objects.filter(user=user).exclude(
        email__iexact=normalized_email
    ).delete()

    email_qs = EmailAddress.objects.filter(
        user=user, email__iexact=normalized_email)
    email_address = email_qs.first()

    if email_address:
        email_qs.exclude(pk=email_address.pk).delete()
    else:
        email_address = EmailAddress(user=user)

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
        request,
        "We've sent a confirmation email. Please verify the new address to activate it.",
    )


def _rarity_for_user(user):
    """Simple 'rarity' badge based on activity volume."""
    post_count = user.blog_posts.count()
    comment_count = user.comments.count()
    total = post_count + comment_count
    if total >= 30 or post_count >= 15:
        return "Legendary"
    if total >= 15 or post_count >= 8:
        return "Epic"
    return "Common"


def _build_stats(user):
    """Aggregate basic activity stats for the profile dashboard."""
    posts = user.blog_posts.all()
    comments = user.comments.all()
    total_posts = posts.count()
    total_comments = comments.count()
    approved_posts = posts.filter(status=BlogPost.STATUS_APPROVED).count()
    approved_comments = comments.filter(status=Comment.STATUS_APPROVED).count()
    reports_received = CommentReport.objects.filter(
        comment__author=user).count()
    reports_made = CommentReport.objects.filter(reported_by=user).count()
    approved_total = approved_posts + approved_comments
    overall_total = total_posts + total_comments
    approval_rate = round((approved_total / overall_total)
                          * 100) if overall_total else 0
    return {
        "total_posts": total_posts,
        "total_comments": total_comments,
        "approved_posts": approved_posts,
        "approved_comments": approved_comments,
        "approval_rate": approval_rate,
        "reports_received": reports_received,
        "reports_made": reports_made,
    }


def profile(request, username):
    """Public profile page (self-view shows private data and pending items)."""
    profile_user = get_object_or_404(User.objects.all(), username=username)
    profile_obj = _get_profile(profile_user)

    is_self = request.user.is_authenticated and request.user.pk == profile_user.pk
    viewer_is_staff = request.user.is_authenticated and request.user.is_staff
    viewer_is_superuser = request.user.is_authenticated and request.user.is_superuser
    can_moderate = request.user.is_authenticated and (
        request.user.is_staff or request.user.is_superuser
    )

    show_private = is_self or viewer_is_superuser

    base_posts = profile_user.blog_posts.select_related("author")
    base_comments = profile_user.comments.select_related("post", "author")

    draft_posts_qs = (
        base_posts.filter(status=BlogPost.STATUS_DRAFT)
        .order_by("-updated_at")
        if is_self
        else BlogPost.objects.none()
    )

    posts_qs = base_posts.exclude(status=BlogPost.STATUS_DRAFT)

    if not (is_self or viewer_is_superuser):
        posts_qs = posts_qs.filter(status=BlogPost.STATUS_APPROVED)
        comments_qs = base_comments.filter(status=Comment.STATUS_APPROVED)
    else:
        posts_qs = base_posts
        comments_qs = base_comments

    posts_qs = posts_qs.order_by("-created_at")
    comments_qs = comments_qs.order_by("-created_at")

    post_paginator = Paginator(posts_qs, 5)
    comment_paginator = Paginator(comments_qs, 5)

    post_page_number = request.GET.get("post_page")
    comment_page_number = request.GET.get("comment_page")

    posts_page = post_paginator.get_page(post_page_number)
    comments_page = comment_paginator.get_page(comment_page_number)

    quick_posts = posts_qs[:5]
    quick_comments = (
        profile_user.comments.select_related(
            "post").order_by("-created_at")[:5]
    )

    admin_links = {}
    if viewer_is_superuser:
        admin_links = {
            "users": reverse("admin:auth_user_changelist"),
            "posts": reverse("admin:blog_blogpost_changelist"),
            "comments": reverse("admin:blog_comment_changelist"),
        }

    context = {
        "profile_user": profile_user,
        "profile": profile_obj,
        "is_self": is_self,
        "can_moderate": can_moderate and not is_self,
        "viewer_is_staff": viewer_is_staff,
        "viewer_is_superuser": viewer_is_superuser,
        "show_private": show_private,
        "posts_page": posts_page,
        "comments_page": comments_page,
        "quick_posts": quick_posts,
        "quick_comments": quick_comments,
        "draft_posts": list(draft_posts_qs),
        "admin_links": admin_links,
        "stats": _build_stats(profile_user),
        "rarity": _rarity_for_user(profile_user),
    }
    return render(request, "accounts/profile.html", context)


@login_required
def profile_edit(request):
    """Edit the current user's profile (names, birth date, bio, avatar)."""
    profile_obj = _get_profile(request.user)

    if request.method == "POST":
        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=profile_obj,
            user=request.user,
        )
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
    """Delete the current account and all related content after confirmation."""
    if request.method == "POST":
        password = (request.POST.get("confirm_password") or "").strip()
        if not request.user.check_password(password):
            messages.error(
                request,
                "Incorrect password. Your account was not deleted.",
            )
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
    """Shortcut: /profile/ -> /profile/<username>/ for the logged-in user."""
    return redirect("accounts:profile", request.user.username)


class VerifiedEmailPasswordChangeView(PasswordChangeView):
    """Require a verified email before allowing password changes."""

    def dispatch(self, request, *args, **kwargs):
        response = ensure_verified_email(request)
        if response is not None:
            return response
        return super().dispatch(request, *args, **kwargs)
