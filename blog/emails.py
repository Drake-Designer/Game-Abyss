# blog/emails.py
"""Email helpers for the blog application."""

from __future__ import annotations

import logging
from typing import Iterable, Sequence

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.urls import reverse

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
except ImportError:  # optional dependency
    SendGridAPIClient = None
    Mail = None

logger = logging.getLogger(__name__)

User = get_user_model()


def _resolve_recipients(emails: Iterable[str]) -> list[str]:
    """Return a clean list of email addresses, removing blanks and duplicates."""
    unique: list[str] = []
    for email in emails:
        if not email:
            continue
        e = email.strip()
        if e and e not in unique:
            unique.append(e)
    return unique


def _send_email(
    subject: str,
    plain_body: str,
    recipients: Sequence[str],
    *,
    html_body: str | None = None,
) -> None:
    """Send email using SendGrid if available, otherwise Django's backend."""
    recipient_list = _resolve_recipients(recipients)
    if not recipient_list:
        logger.info("Skipping email '%s' - no recipients", subject)
        return

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)

    api_key = getattr(settings, "SENDGRID_API_KEY", "")
    if api_key and SendGridAPIClient and Mail and not getattr(settings, "DEBUG", False):
        try:
            message = Mail(
                from_email=from_email,
                to_emails=recipient_list,
                subject=subject,
                plain_text_content=plain_body,
                html_content=html_body or plain_body.replace("\n", "<br>"),
            )
            SendGridAPIClient(api_key).send(message)
            return
        except Exception as exc:  # best effort
            logger.exception(
                "SendGrid error while sending '%s': %s", subject, exc)

    send_mail(
        subject=subject,
        message=plain_body,
        from_email=from_email,
        recipient_list=recipient_list,
        fail_silently=True,
        html_message=html_body,
    )


def get_primary_superadmin_email() -> list[str]:
    """Return the primary super admin email if configured or fallback to DB."""
    configured = getattr(settings, "PRIMARY_SUPERADMIN_EMAIL", "")
    if configured:
        return [configured]
    qs = User.objects.filter(
        is_superuser=True, is_active=True).exclude(email="")
    return list(qs.values_list("email", flat=True))


def get_staff_recipients() -> list[str]:
    """Return active staff emails for moderation alerts."""
    qs = User.objects.filter(is_staff=True, is_active=True).exclude(email="")
    return list(qs.values_list("email", flat=True))


def notify_superadmins_new_post(post) -> None:
    subject = "[Game Abyss] New post submitted"
    post_url = post.get_absolute_url()
    plain_body = (
        "Hello Council,\n\n"
        f"{post.author.get_username()} just submitted a new post titled \"{post.title}\".\n"
        f"Current status: {post.get_status_display()}.\n"
        f"Preview: {post_url}\n"
    )
    _send_email(subject, plain_body, get_primary_superadmin_email())


def notify_superadmins_new_comment(comment) -> None:
    subject = "[Game Abyss] New comment submitted"
    post_url = comment.post.get_absolute_url()
    plain_body = (
        "Hello Council,\n\n"
        f"{comment.author.get_username()} left a new comment on \"{comment.post.title}\".\n"
        f"Excerpt: {comment.body[:200]}\n"
        f"Moderate on: {post_url}\n"
    )
    _send_email(subject, plain_body, get_primary_superadmin_email())


def notify_author_post_approved(post) -> None:
    if not getattr(post.author, "email", ""):
        return
    subject = "[Game Abyss] Your post was approved"
    post_url = post.get_absolute_url()
    plain_body = (
        f"Explorer {post.author.get_username()},\n\n"
        f"The Council has approved your post \"{post.title}\". It now echoes across the Abyss, visible on the front page.\n"
        f"Read it here: {post_url}\n\n"
        "Keep the signals coming."
    )
    _send_email(subject, plain_body, [post.author.email])


def notify_author_post_featured(post) -> None:
    if not getattr(post.author, "email", ""):
        return
    subject = "[Game Abyss] Your post is Featured"
    post_url = post.get_absolute_url()
    plain_body = (
        f"Explorer {post.author.get_username()},\n\n"
        f"Your post \"{post.title}\" has been marked as Featured by the Council.\n"
        f"See it in the spotlight: {post_url}\n\n"
        "Thanks for powering the community."
    )
    _send_email(subject, plain_body, [post.author.email])


def notify_author_post_rejected(post) -> None:
    if not getattr(post.author, "email", ""):
        return
    subject = "[Game Abyss] Your post was rejected"
    plain_body = (
        f"Explorer {post.author.get_username()},\n\n"
        f"Your post \"{post.title}\" was not approved this round, so it will not be visible on the blog.\n"
        "Refine the piece and resubmit when ready.\n\n"
        "The Game Abyss Council"
    )
    _send_email(subject, plain_body, [post.author.email])


def notify_staff_comment_report(report) -> None:
    recipients = get_staff_recipients()
    if not recipients:
        return
    subject = "[Game Abyss] Comment reported"
    moderation_url = reverse(
        "admin:blog_comment_change", args=[report.comment.pk])
    plain_body = (
        "Heads up, team,\n\n"
        f"{report.reported_by.get_username()} reported a comment on \"{report.comment.post.title}\".\n"
        f"Reason: {report.get_reason_display()}.\n"
        f"Open moderation: {moderation_url}\n"
    )
    _send_email(subject, plain_body, recipients)
