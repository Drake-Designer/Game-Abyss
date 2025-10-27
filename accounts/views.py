from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.decorators import login_required
from allauth.account.models import EmailAddress
from allauth.account.views import PasswordChangeView
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from blog.models import BlogPost, Comment

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


def profile(request, username):
    """Public profile page showing a user's activity."""
    profile_user = get_object_or_404(
        User.objects.select_related("profile"),
        username=username,
    )
    profile_obj = _get_profile(profile_user)

    is_self = request.user.is_authenticated and request.user.pk == profile_user.pk

    public_posts_qs = (
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

    post_paginator = Paginator(public_posts_qs, 5)
    comment_paginator = Paginator(approved_comments_qs, 5)

    posts_page = post_paginator.get_page(request.GET.get("post_page"))
    comments_page = comment_paginator.get_page(request.GET.get("comment_page"))

    stats = {
        "public_posts": public_posts_qs.count(),
        "approved_comments": approved_comments_qs.count(),
    }

    full_name = (profile_user.get_full_name() or "").strip() or None

    context = {
        "profile_user": profile_user,
        "profile": profile_obj,
        "is_self": is_self,
        "full_name": full_name,
        "posts_page": posts_page,
        "comments_page": comments_page,
        "draft_posts": draft_posts,
        "stats": stats,
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
    """Shortcut: /profile/ -> /u/<username>/ for the logged-in user."""
    return redirect("accounts:profile", request.user.username)


class VerifiedEmailPasswordChangeView(PasswordChangeView):
    """Require a verified email before allowing password changes."""

    def dispatch(self, request, *args, **kwargs):
        response = ensure_verified_email(request)
        if response is not None:
            return response
        return super().dispatch(request, *args, **kwargs)
