"""Utility helpers for sending themed Game Abyss emails."""

from __future__ import annotations

import logging
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import Iterable, Sequence
from urllib.parse import urljoin

# Django imports first, grouped
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

# Optional third-party imports, safely loaded
try:  # pragma: no cover
    SENDGRID = import_module("sendgrid")
    SG_HELPERS_MAIL = import_module("sendgrid.helpers.mail")
    SG_CLIENT_CLS = SENDGRID.SendGridAPIClient  # type: ignore[attr-defined]
    SG_MAIL_CLS = SG_HELPERS_MAIL.Mail  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover
    SG_CLIENT_CLS = None  # type: ignore[assignment]
    SG_MAIL_CLS = None  # type: ignore[assignment]

try:  # pragma: no cover
    PREMAILER = import_module("premailer")
    CSS_INLINE_TRANSFORM = getattr(PREMAILER, "transform", None)
except ImportError:  # pragma: no cover
    CSS_INLINE_TRANSFORM = None

try:  # pragma: no cover
    from django.contrib.sites.models import Site as SITES_MODEL  # type: ignore
except ImportError:  # pragma: no cover
    SITES_MODEL = None  # type: ignore

try:  # pragma: no cover
    from django.contrib.staticfiles import finders as STATIC_FINDERS  # type: ignore
except ImportError:  # pragma: no cover
    STATIC_FINDERS = None  # type: ignore


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
    scheme = getattr(settings, "SITE_SCHEME", None) or (
        "https" if not getattr(settings, "DEBUG", False) else "http"
    )

    if not base_url:
        domain = getattr(settings, "SITE_DOMAIN", "").strip()
        if domain:
            base_url = f"{scheme}://{domain}"
        elif SITES_MODEL is not None:
            try:
                site = SITES_MODEL.objects.get_current()
                domain = site.domain.strip()
                if domain:
                    base_url = (
                        domain
                        if domain.startswith(("http://", "https://"))
                        else f"{scheme}://{domain}"
                    )
            except (ImproperlyConfigured, ObjectDoesNotExist):
                logger.debug(
                    "Sites framework not configured; falling back to ALLOWED_HOSTS"
                )
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

    # Try staticfiles finders
    if STATIC_FINDERS is not None:  # pragma: no cover
        try:
            resolved = STATIC_FINDERS.find(stylesheet_setting)
        except OSError:
            resolved = None
            logger.exception("Staticfiles finder failed for email stylesheet")
        if resolved:
            if isinstance(resolved, (list, tuple)):
                candidate_paths.extend(Path(p) for p in resolved if p)
            else:
                candidate_paths.append(Path(resolved))

    # STATIC_ROOT
    static_root = getattr(settings, "STATIC_ROOT", None)
    if static_root:
        candidate_paths.append(Path(static_root) / stylesheet_setting)

    # STATICFILES_DIRS
    for directory in getattr(settings, "STATICFILES_DIRS", []):
        candidate_paths.append(Path(directory) / stylesheet_setting)

    # BASE_DIR/static
    base_dir = getattr(settings, "BASE_DIR", None)
    if base_dir:
        candidate_paths.append(Path(base_dir) / "static" / stylesheet_setting)

    for path in candidate_paths:
        try:
            if path.is_file():
                return path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            logger.exception("Unable to read email stylesheet from %s", path)

    logger.warning("Email stylesheet '%s' could not be located",
                   stylesheet_setting)
    return None


def _inject_css(html: str, css_text: str | None) -> str:
    """Embed CSS in the HTML head for clients without inlining support."""
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
    Inline styles for better email client compatibility using Premailer
    if available; otherwise return the original HTML with an embedded <style>.
    """
    html_with_css = _inject_css(html, css_text)

    if CSS_INLINE_TRANSFORM is None:
        return html_with_css
    try:
        transform_kwargs = {"remove_classes": False}
        if base_url:
            transform_kwargs["base_url"] = base_url
        return CSS_INLINE_TRANSFORM(html_with_css, **transform_kwargs)
    except (ValueError, OSError):
        logger.exception(
            "Premailer failed; sending email without CSS inlining.")
        return html_with_css


def _build_email_context(subject: str, context: dict) -> dict:
    """Create the final template context with site defaults."""
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
    final = {**base_context, **context}

    # Normalize CTA
    cta = final.get("cta")
    if isinstance(cta, dict) and cta.get("url"):
        final["cta"] = {**cta, "url": build_absolute_uri(cta.get("url"))}

    # Normalize detail items
    detail_items = final.get("detail_items")
    if isinstance(detail_items, (list, tuple)):
        normalized: list[dict] = []
        for item in detail_items:
            if not isinstance(item, dict):
                continue
            record = {**item}
            if record.get("url"):
                record["url"] = build_absolute_uri(record["url"])
            normalized.append(record)
        final["detail_items"] = normalized

    return final


def _send_via_sendgrid(
    subject: str,
    text_body: str,
    html_body: str,
    recipient_list: Sequence[str],
    from_email: str | None,
) -> bool:
    """Send using SendGrid if available; return True on success."""
    api_key = getattr(settings, "SENDGRID_API_KEY", "")
    have_client = SG_CLIENT_CLS is not None and SG_MAIL_CLS is not None
    if not api_key or not have_client or getattr(settings, "DEBUG", False):
        return False
    try:
        message = SG_MAIL_CLS(  # type: ignore[call-arg]
            from_email=from_email,
            to_emails=recipient_list,
            subject=subject,
            plain_text_content=text_body,
            html_content=html_body,
        )
        # type: ignore[operator]
        SG_CLIENT_CLS(api_key).send(message)
        return True
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.exception("SendGrid error while sending '%s': %s", subject, exc)
        return False


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

    final_context = _build_email_context(subject, context)
    site_url = final_context.get("site_url") or ""

    html_body_raw = render_to_string(template_name, final_context)
    css_text = _load_email_stylesheet()
    html_body = _inline_css_if_possible(
        html_body_raw,
        base_url=site_url or None,
        css_text=css_text,
    )
    text_body = (
        render_to_string(text_template, final_context)
        if text_template
        else strip_tags(html_body)
    )

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)

    if _send_via_sendgrid(
        subject,
        text_body,
        html_body,
        recipient_list,
        from_email,
    ):
        return

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_email,
        to=recipient_list,
    )
    email.attach_alternative(html_body, "text/html")
    email.send(fail_silently=True)
