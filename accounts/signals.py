# ============================================================
# *** ACCOUNTS SIGNALS: Account lifecycle events ***
# ============================================================

"""Signals for account lifecycle events."""

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.urls import reverse

from core.emailing import build_absolute_uri, send_styled_email

User = get_user_model()


def _collect_staff_recipients(exclude_user_ids=None):
    """Return unique email addresses for all staff and superusers."""
    qs = User.objects.filter(Q(is_staff=True) | Q(
        is_superuser=True)).exclude(email="")
    if exclude_user_ids:
        qs = qs.exclude(pk__in=exclude_user_ids)
    emails = qs.values_list("email", flat=True)
    return list(set(emails))


def _notify_staff(subject, context, exclude_user_ids=None):
    """Send a styled notification to all staff and superusers."""
    recipients = _collect_staff_recipients(exclude_user_ids)
    if not recipients:
        return
    send_styled_email(
        subject,
        "emails/notification.html",
        context,
        recipients,
        text_template="emails/notification.txt",
    )


@receiver(post_save, sender=User, dispatch_uid="accounts_user_created_notify")
def notify_staff_user_registered(sender, instance, created, **kwargs):
    """Notify staff when a new user account is created."""
    if not created:
        return
    subject = f"New user registered: {instance.username}"
    detail_items = [{"label": "Username", "value": instance.username}]
    if instance.email:
        detail_items.append({"label": "Email", "value": instance.email})
    if instance.get_full_name():
        detail_items.append(
            {"label": "Name", "value": instance.get_full_name()})

    profile_url = build_absolute_uri(
        reverse("admin:auth_user_change", args=[instance.pk])
    )
    context = {
        "greeting": "Hello Council,",
        "intro": "A new explorer has registered on Game Abyss.",
        "detail_items": detail_items,
        "cta": {"label": "View in admin", "url": profile_url},
        "closing": "Welcome them to the community!",
        "signature": "Game Abyss Alerts",
        "footer_note": "Notification for Game Abyss staff.",
    }
    _notify_staff(subject, context, exclude_user_ids=[instance.pk])


@receiver(post_delete, sender=User, dispatch_uid="accounts_user_deleted_notify")
def notify_staff_user_deleted(sender, instance, **kwargs):
    """Notify staff when a user account is deleted."""
    subject = f"User account deleted: {instance.username}"
    detail_items = [{"label": "Username", "value": instance.username}]
    if instance.email:
        detail_items.append({"label": "Email", "value": instance.email})

    user_list_url = build_absolute_uri(reverse("admin:auth_user_changelist"))
    context = {
        "greeting": "Heads up, team,",
        "intro": "A user account has been removed from Game Abyss.",
        "detail_items": detail_items,
        "cta": {"label": "Open user directory", "url": user_list_url},
        "closing": "Audit complete? Log the change if needed.",
        "signature": "Game Abyss Alerts",
        "footer_note": "Notification for Game Abyss staff.",
    }
    _notify_staff(subject, context)
