"""Email helpers for the contact/help request workflow."""

from __future__ import annotations

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from core.emailing import build_absolute_uri, send_styled_email


def _support_recipients() -> list[str]:
    """Return email addresses that should receive help notifications."""

    recipients: list[str] = []
    primary = getattr(settings, "PRIMARY_SUPERADMIN_EMAIL", "").strip()
    support = getattr(settings, "SUPPORT_EMAIL", "").strip()
    for candidate in (support, primary):
        if candidate and candidate not in recipients:
            recipients.append(candidate)
    return recipients or ["team.gameabyss@gmail.com"]


def notify_support_new_help_request(help_request) -> None:
    """Send a notification to staff when a help request is submitted."""

    recipients = _support_recipients()
    admin_url = build_absolute_uri(
        reverse("admin:pages_helprequest_change", args=[help_request.pk])
    )
    inbox_url = build_absolute_uri(
        reverse("admin:pages_helprequest_changelist"))
    context = {
        "greeting": "Hello support team,",
        "intro": "A new help request has been submitted on Game Abyss.",
        "body_lines": [
            f"Subject: {help_request.subject}",
            f"Priority: {help_request.get_priority_display()}",
        ],
        "detail_items": [
            {"label": "Name", "value": help_request.name or "Anonymous"},
            {"label": "Email", "value": help_request.email or "Not provided"},
            {
                "label": "Admin link",
                "value": admin_url,
                "url": admin_url,
            },
            {
                "label": "All help requests",
                "value": inbox_url,
                "url": inbox_url,
            },
        ],
        "cta": {"label": "Review request", "url": admin_url},
        "closing": "Thanks for helping the community stay supported.",
        "signature": "Game Abyss",
        "footer_note": "You received this because you are listed as support staff.",
    }
    send_styled_email(
        "[Game Abyss] New help request",
        "emails/notification.html",
        context,
        recipients,
        text_template="emails/notification.txt",
    )


def send_help_request_confirmation(help_request) -> None:
    """Send a confirmation email to the requester if an address was provided."""

    email = (help_request.email or "").strip()
    if not email:
        return

    contact_url = build_absolute_uri(reverse("pages:contact"))
    submitted_at = timezone.localtime(help_request.created_at)
    context = {
        "greeting": f"Hi {help_request.name or 'explorer'},",
        "intro": "Thanks for contacting the Game Abyss support team.",
        "body_lines": [
            "We received your message and a staff member will reply soon.",
            f"Subject: {help_request.subject}",
            f"Priority: {help_request.get_priority_display()}",
        ],
        "detail_items": [
            {
                "label": "Submitted on",
                "value": submitted_at.strftime("%d %B %Y %H:%M"),
            },
        ],
        "cta": {"label": "Update your details", "url": contact_url},
        "closing": "Stay tuned – we'll be in touch shortly.",
        "signature": "The Game Abyss Support Team",
        "footer_note": "You are receiving this because you submitted a help request on Game Abyss.",
    }
    send_styled_email(
        "[Game Abyss] We received your help request",
        "emails/notification.html",
        context,
        [email],
        text_template="emails/notification.txt",
    )
