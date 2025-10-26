"""Utility helpers for account-related features."""

from functools import wraps

from allauth.account.models import EmailAddress
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse


EMAIL_VERIFICATION_REQUIRED_MESSAGE = (
    "Please verify your email address before continuing. "
    "Check your inbox for the confirmation link or request a new one "
    "from the Email Addresses page."
)


def user_email_is_verified(user) -> bool:
    """Return True when the user has at least one verified email address."""
    email = getattr(user, "email", "") or ""
    if not email:
        # Users without an email address bypass the verification requirement
        return True

    email_qs = EmailAddress.objects.filter(user=user)
    if not email_qs.exists():
        return False

    return email_qs.filter(verified=True).exists()


def ensure_verified_email(request: HttpRequest) -> HttpResponse | None:
    """Redirect to the email management page when verification is required."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return None

    if user_email_is_verified(user):
        return None

    messages.error(request, EMAIL_VERIFICATION_REQUIRED_MESSAGE)
    return redirect(reverse("account_email"))


def verified_email_required(view_func):
    """Decorator ensuring the logged-in user has a verified email address."""

    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs):
        response = ensure_verified_email(request)
        if response is not None:
            return response
        return view_func(request, *args, **kwargs)

    return _wrapped
