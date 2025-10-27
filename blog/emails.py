"""Email helpers for the blog application."""

from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from core.emailing import build_absolute_uri, send_styled_email

User = get_user_model()


def _truncate_excerpt(text: str, limit: int = 200) -> str:
    """Return a shortened text excerpt with a default message."""
    excerpt = (text or "").strip()
    if len(excerpt) > limit:
        excerpt = excerpt[: limit - 3].rstrip() + "..."
    return excerpt or "No additional text provided."


def get_primary_superadmin_email() -> list[str]:
    """Return the primary superadmin email address."""
    configured = getattr(settings, "PRIMARY_SUPERADMIN_EMAIL", "")
    if configured:
        return [configured]
    qs = User.objects.filter(
        is_superuser=True, is_active=True).exclude(email="")
    return list(qs.values_list("email", flat=True))


def get_staff_recipients() -> list[str]:
    """Return staff emails for moderation alerts."""
    qs = User.objects.filter(is_staff=True, is_active=True).exclude(email="")
    return list(qs.values_list("email", flat=True))


def notify_superadmins_new_post(post) -> None:
    """Notify superadmins when a new post is submitted."""
    subject = "[Game Abyss] New post submitted"
    admin_url = build_absolute_uri(reverse("admin:blog_blogpost_changelist"))
    post_admin_url = build_absolute_uri(
        reverse("admin:blog_blogpost_change", args=[post.pk])
    )
    context = {
        "greeting": "Hello Council,",
        "intro": (
            f"{post.author.get_username()} just submitted a new post titled "
            f"\"{post.title}\"."
        ),
        "body_lines": [
            f"Current status: {post.get_status_display()}.",
        ],
        "detail_items": [
            {"label": "Author", "value": post.author.get_username()},
            {"label": "Status", "value": post.get_status_display()},
            {"label": "Post (admin)", "value": post_admin_url,
             "url": post_admin_url},
            {"label": "All posts", "value": admin_url, "url": admin_url},
        ],
        "cta": {"label": "Review submission", "url": post_admin_url},
        "closing": "Thanks for keeping the Abyss curated.",
        "signature": "The Game Abyss Council",
        "footer_note": "Notification for Game Abyss superadmins.",
    }
    send_styled_email(
        subject,
        "emails/notification.html",
        context,
        get_primary_superadmin_email(),
        text_template="emails/notification.txt",
    )


def notify_superadmins_new_comment(comment) -> None:
    """Notify superadmins when a new comment is submitted."""
    subject = "[Game Abyss] New comment submitted"
    comment_admin_url = build_absolute_uri(
        reverse("admin:blog_comment_change", args=[comment.pk])
    )
    post_admin_url = build_absolute_uri(
        reverse("admin:blog_blogpost_change", args=[comment.post.pk])
    )
    context = {
        "greeting": "Hello Council,",
        "intro": (
            f"{comment.author.get_username()} left a new comment on "
            f"\"{comment.post.title}\"."
        ),
        "body_lines": [
            f"Excerpt: {_truncate_excerpt(comment.body)}",
        ],
        "detail_items": [
            {"label": "Commenter", "value": comment.author.get_username()},
            {"label": "Post (admin)", "value": post_admin_url,
             "url": post_admin_url},
            {"label": "Status", "value": comment.get_status_display()},
        ],
        "cta": {"label": "Moderate comment", "url": comment_admin_url},
        "closing": "Stay vigilant, council members.",
        "signature": "Game Abyss Moderation",
        "footer_note": "Notification for Game Abyss superadmins.",
    }
    send_styled_email(
        subject,
        "emails/notification.html",
        context,
        get_primary_superadmin_email(),
        text_template="emails/notification.txt",
    )


def notify_author_post_approved(post) -> None:
    """Notify the author when a post is approved."""
    if not getattr(post.author, "email", ""):
        return
    subject = "[Game Abyss] Your post was approved"
    post_url = build_absolute_uri(post.get_absolute_url())
    context = {
        "greeting": f"Explorer {post.author.get_username()},",
        "intro": "The Council has approved your latest transmission.",
        "body_lines": [
            f"Title: \"{post.title}\"",
            "It now echoes across the Abyss and appears on the front page.",
        ],
        "detail_items": [
            {"label": "View your post", "value": post_url, "url": post_url},
        ],
        "cta": {"label": "Read it on Game Abyss", "url": post_url},
        "closing": "Keep the signals coming.",
        "signature": "The Game Abyss Council",
        "footer_note": "You are receiving this email because you published on Game Abyss.",
    }
    send_styled_email(
        subject,
        "emails/notification.html",
        context,
        [post.author.email],
        text_template="emails/notification.txt",
    )


def notify_author_post_featured(post) -> None:
    """Notify the author when a post is featured."""
    if not getattr(post.author, "email", ""):
        return
    subject = "[Game Abyss] Your post is Featured"
    post_url = build_absolute_uri(post.get_absolute_url())
    context = {
        "greeting": f"Explorer {post.author.get_username()},",
        "intro": "Your post was marked as Featured.",
        "body_lines": [
            f"Title: \"{post.title}\"",
            "Expect a surge of eyes on your signal!",
        ],
        "detail_items": [
            {"label": "Featured link", "value": post_url, "url": post_url},
        ],
        "cta": {"label": "View the feature", "url": post_url},
        "closing": "Thanks for powering the community.",
        "signature": "The Game Abyss Council",
        "footer_note": "You are receiving this email because you published on Game Abyss.",
    }
    send_styled_email(
        subject,
        "emails/notification.html",
        context,
        [post.author.email],
        text_template="emails/notification.txt",
    )


def notify_author_post_rejected(post) -> None:
    """Notify the author when a post is rejected."""
    if not getattr(post.author, "email", ""):
        return
    subject = "[Game Abyss] Your post was rejected"
    context = {
        "greeting": f"Explorer {post.author.get_username()},",
        "intro": "The Council reviewed your post but it won't surface this round.",
        "body_lines": [
            f"Title: \"{post.title}\"",
            "Tighten the signal and submit again when you're ready.",
        ],
        "closing": "We're looking forward to your next transmission.",
        "signature": "The Game Abyss Council",
        "footer_note": "You are receiving this email because you published on Game Abyss.",
    }
    send_styled_email(
        subject,
        "emails/notification.html",
        context,
        [post.author.email],
        text_template="emails/notification.txt",
    )


def notify_staff_comment_report(report) -> None:
    """Notify staff when a comment is reported."""
    recipients = get_staff_recipients()
    if not recipients:
        return
    subject = "[Game Abyss] Comment reported"
    comment_admin_url = build_absolute_uri(
        reverse("admin:blog_comment_change", args=[report.comment.pk])
    )
    post_admin_url = build_absolute_uri(
        reverse("admin:blog_blogpost_change", args=[report.comment.post.pk])
    )
    context = {
        "greeting": "Heads up, team,",
        "intro": (
            f"{report.reported_by.get_username()} flagged a comment on "
            f"\"{report.comment.post.title}\"."
        ),
        "body_lines": [
            f"Reason provided: {report.get_reason_display()}.",
            f"Comment excerpt: {_truncate_excerpt(report.comment.body)}",
        ],
        "detail_items": [
            {"label": "Post (admin)", "value": post_admin_url,
             "url": post_admin_url},
            {"label": "Reporter", "value": report.reported_by.get_username()},
            {"label": "Comment author", "value": report.comment.author.get_username()},
        ],
        "cta": {"label": "Open in admin", "url": comment_admin_url},
        "closing": "Thanks for watching the Abyss gates.",
        "signature": "Game Abyss Moderation",
        "footer_note": "Notification for Game Abyss staff.",
    }
    send_styled_email(
        subject,
        "emails/notification.html",
        context,
        recipients,
        text_template="emails/notification.txt",
    )
