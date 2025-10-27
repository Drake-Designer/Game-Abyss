"""Utility helpers for sending themed Game Abyss emails."""

from __future__ import annotations

import logging
from typing import Iterable, Sequence
from urllib.parse import urljoin

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

# Optional: SendGrid backend
try:  # pragma: no cover - optional dependency
    from sendgrid import SendGridAPIClient  # type: ignore
    from sendgrid.helpers.mail import Mail  # type: ignore
except ImportError:  # pragma: no cover
    SendGridAPIClient = None  # type: ignore
    Mail = None  # type: ignore

# Optional: Sites framework (may not be present in tests)
try:  # pragma: no cover - best effort
    from django.contrib.sites.models import Site  # type: ignore
except Exception:  # pragma: no cover
    Site = None  # type: ignore

# Optional: premailer for CSS inlining
try:  # pragma: no cover - optional dependency
    from premailer import transform  # type: ignore
except Exception:  # pragma: no cover
    transform = None  # type: ignore

logger = logging.getLogger(__name__)


def _resolve_recipients(emails: Iterable[str]) -> list[str]:
    """Return a clean list of email addresses, removing blanks and duplicates."""
    unique: list[str] = []
    for email in emails:
        if not email:
            continue
        trimmed = email.strip()
        if trimmed and trimmed not in unique:
            unique.append(trimmed)
    return unique


def build_absolute_uri(path: str | None) -> str | None:
    """Return an absolute URL for the given path if possible."""
    if not path:
        return None

    if path.startswith(("http://", "https://")):
        return path

    base_url = getattr(settings, "SITE_BASE_URL", "").strip()
    if not base_url:
        scheme = getattr(settings, "SITE_SCHEME", None) or (
            "https" if not getattr(settings, "DEBUG", False) else "http"
        )
        domain = getattr(settings, "SITE_DOMAIN", "").strip()
        if domain:
            base_url = f"{scheme}://{domain}"
        elif Site is not None:
            try:
                site = Site.objects.get_current()
                domain = site.domain.strip()
                if domain:
                    if domain.startswith(("http://", "https://")):
                        base_url = domain
                    else:
                        base_url = f"{scheme}://{domain}"
            except Exception:
                logger.debug("Falling back to ALLOWED_HOSTS for email URLs")
        if not base_url:
            allowed_hosts = getattr(settings, "ALLOWED_HOSTS", [])
            if allowed_hosts:
                base_url = f"{scheme}://{allowed_hosts[0]}"
    if not base_url:
        return path

    return urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))


def _inline_css_if_possible(html: str) -> str:
    """
    Inline styles for better email client compatibility using premailer
    if available; otherwise return the original HTML.
    """
    if transform is None:
        return html
    try:
        # keep class names for tests
        return transform(html, remove_classes=False)
    except Exception:
        logger.exception(
            "Premailer failed; sending email without CSS inlining.")
        return html


def send_styled_email(
    subject: str,
    template_name: str,
    context: dict,
    recipients: Sequence[str],
    *,
    text_template: str | None = None,
) -> None:
    """Render and deliver a styled Game Abyss email."""
    recipient_list = _resolve_recipients(recipients)
    if not recipient_list:
        logger.info("Skipping email '%s' - no recipients", subject)
        return

    support_email = getattr(
        settings,
        "SUPPORT_EMAIL",
        getattr(settings, "PRIMARY_SUPERADMIN_EMAIL",
                "team.gameabyss@gmail.com"),
    )
    base_context = {
        "subject": subject,
        "site_name": "Game Abyss",
        "support_email": support_email,
        "site_url": build_absolute_uri("/") or "",
        "accent_color": "#ff6b35",
        "surface_color": "#1a1a24",
        "dark_color": "#0a0a0f",
        "current_year": timezone.now().year,
    }
    final_context = {**base_context, **context}

    # Normalise CTA URL if present
    cta = final_context.get("cta")
    if isinstance(cta, dict) and cta.get("url"):
        final_context["cta"] = {
            **cta, "url": build_absolute_uri(cta.get("url"))}

    # Normalise detail item URLs
    detail_items = final_context.get("detail_items")
    if isinstance(detail_items, (list, tuple)):
        normalised: list[dict] = []
        for item in detail_items:
            if not isinstance(item, dict):
                continue
            record = {**item}
            if record.get("url"):
                record["url"] = build_absolute_uri(record["url"])
            normalised.append(record)
        final_context["detail_items"] = normalised

    # Render HTML and plain text
    html_body_raw = render_to_string(template_name, final_context)
    html_body = _inline_css_if_possible(html_body_raw)
    if text_template:
        text_body = render_to_string(text_template, final_context)
    else:
        text_body = strip_tags(html_body)

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)

    # Try SendGrid first (production), then fallback to Django backend
    api_key = getattr(settings, "SENDGRID_API_KEY", "")
    if (
        api_key
        and SendGridAPIClient is not None
        and Mail is not None
        and not getattr(settings, "DEBUG", False)
    ):
        try:
            message = Mail(
                from_email=from_email,
                to_emails=recipient_list,
                subject=subject,
                plain_text_content=text_body,
                html_content=html_body,
            )
            SendGridAPIClient(api_key).send(message)
            return
        except Exception:
            logger.exception("SendGrid error while sending '%s'", subject)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_email,
        to=recipient_list,
    )
    email.attach_alternative(html_body, "text/html")
    email.send(fail_silently=True)
