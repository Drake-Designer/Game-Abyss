"""Utility helpers for sending themed Game Abyss emails."""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
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

# Optional: access to the Django staticfiles finders for loading CSS
try:  # pragma: no cover - optional dependency
    from django.contrib.staticfiles import finders  # type: ignore
except Exception:  # pragma: no cover
    finders = None  # type: ignore

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


@lru_cache(maxsize=1)
def _load_email_stylesheet() -> str | None:
    """Return the contents of the email stylesheet if available."""
    stylesheet_setting = getattr(
        settings, "EMAIL_STYLESHEET_PATH", "css/email.css")

    candidate_paths: list[Path] = []

    # Try staticfiles finders first (if available)
    if finders is not None:  # pragma: no cover - not easily testable
        try:
            resolved = finders.find(stylesheet_setting)
        except Exception:
            resolved = None
            logger.exception("Staticfiles finder failed for email stylesheet")
        if resolved:
            if isinstance(resolved, (list, tuple)):
                candidate_paths.extend(Path(p) for p in resolved if p)
            else:
                candidate_paths.append(Path(resolved))

    # Then STATIC_ROOT
    static_root = getattr(settings, "STATIC_ROOT", None)
    if static_root:
        candidate_paths.append(Path(static_root) / stylesheet_setting)

    # Then STATICFILES_DIRS
    for directory in getattr(settings, "STATICFILES_DIRS", []):
        candidate_paths.append(Path(directory) / stylesheet_setting)

    # Finally BASE_DIR/static
    base_dir = getattr(settings, "BASE_DIR", None)
    if base_dir:
        candidate_paths.append(Path(base_dir) / "static" / stylesheet_setting)

    for path in candidate_paths:
        try:
            if path.is_file():
                return path.read_text(encoding="utf-8")
        except Exception:
            logger.exception("Unable to read email stylesheet from %s", path)

    logger.warning("Email stylesheet '%s' could not be located",
                   stylesheet_setting)
    return None


def _inject_css(html: str, css_text: str | None) -> str:
    """Embed CSS inside the HTML <head> for clients without inlining support."""
    if not css_text:
        return html

    style_block = '<style type="text/css">\n' + css_text + "\n</style>"
    head_close = "</head>"
    if head_close in html:
        return html.replace(head_close, f"{style_block}\n{head_close}", 1)
    return f"{style_block}\n{html}"


def _inline_css_if_possible(
    html: str, *, base_url: str | None = None, css_text: str | None = None
) -> str:
    """
    Inline styles for better email client compatibility using premailer
    if available; otherwise return the original HTML with an embedded <style>.
    """
    html_with_css = _inject_css(html, css_text)

    if transform is None:
        return html_with_css
    try:
        transform_kwargs = {"remove_classes": False}
        if base_url:
            transform_kwargs["base_url"] = base_url
        return transform(html_with_css, **transform_kwargs)
    except Exception:
        logger.exception(
            "Premailer failed; sending email without CSS inlining.")
        return html_with_css


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
    site_url = build_absolute_uri("/") or ""

    base_context = {
        "subject": subject,
        "site_name": "Game Abyss",
        "support_email": support_email,
        "site_url": site_url,
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
    css_text = _load_email_stylesheet()
    html_body = _inline_css_if_possible(
        html_body_raw, base_url=site_url or None, css_text=css_text
    )
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
        except Exception:  # pragma: no cover - optional backend failure
            logger.exception("SendGrid error while sending '%s'", subject)

    # Fallback: Django email backend
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_email,
        to=recipient_list,
    )
    email.attach_alternative(html_body, "text/html")
    email.send(fail_silently=True)
