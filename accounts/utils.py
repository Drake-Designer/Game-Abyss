# ============================================================
# *** ACCOUNTS UTILS: Utility helpers for account features ***
# ============================================================

"""Utility helpers for account-related features."""

from functools import wraps
from typing import Callable, Optional

from allauth.account.models import EmailAddress
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse

from blog.models import BlogPost, Comment, CommentReport, log_moderation_action

# ============================================================
# Email verification checks
# ============================================================

EMAIL_VERIFICATION_REQUIRED_MESSAGE = (
    "Please verify your email to continue. Check your inbox for our confirmation link, "
    "or request a new one from the Email Addresses page."
)


def user_email_is_verified(user) -> bool:
    """Return True when the user has at least one verified email address."""
    email = getattr(user, "email", "") or ""
    if not email:
        # If the account has no email, do not block flows
        return True

    email_qs = EmailAddress.objects.filter(user=user)
    if not email_qs.exists():
        return False

    return email_qs.filter(verified=True).exists()


def ensure_verified_email(request: HttpRequest) -> Optional[HttpResponse]:
    """Redirect to the email management page when verification is required."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return None

    if user_email_is_verified(user):
        return None

    messages.error(request, EMAIL_VERIFICATION_REQUIRED_MESSAGE)
    return redirect(reverse("account_email"))


def verified_email_required(view_func: Callable) -> Callable:
    """Decorator ensuring the logged-in user has a verified email address."""

    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs):
        response = ensure_verified_email(request)
        if response is not None:
            return response
        return view_func(request, *args, **kwargs)

    return _wrapped


# ============================================================
# Moderation helpers
# ============================================================

def approve_post(actor, post: BlogPost, notes: str = "") -> None:
    """Mark a blog post as approved."""
    post.status = BlogPost.STATUS_APPROVED
    post.save(update_fields=["status", "updated_at"])
    log_moderation_action(actor, "approve_post", post, notes)


def reject_post(actor, post: BlogPost, notes: str = "") -> None:
    """Mark a blog post as rejected."""
    post.status = BlogPost.STATUS_REJECTED
    post.save(update_fields=["status", "updated_at"])
    log_moderation_action(actor, "reject_post", post, notes)


def approve_comment(actor, comment: Comment, notes: str = "") -> None:
    """Mark a comment as approved."""
    comment.status = Comment.STATUS_APPROVED
    comment.save(update_fields=["status", "updated_at"])
    log_moderation_action(actor, "approve_comment", comment, notes)


def reject_comment(actor, comment: Comment, notes: str = "") -> None:
    """Mark a comment as rejected."""
    comment.status = Comment.STATUS_REJECTED
    comment.save(update_fields=["status", "updated_at"])
    log_moderation_action(actor, "reject_comment", comment, notes)


def resolve_report(actor, report: CommentReport, notes: str = "") -> None:
    """Mark a report as resolved."""
    report.resolved = True
    report.save(update_fields=["resolved", "updated_at"] if hasattr(
        report, "updated_at") else ["resolved"])
    log_moderation_action(actor, "resolve_report", report, notes)
