"""Signals for account lifecycle events."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models import Q
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

User = get_user_model()


def _collect_staff_recipients(exclude_user_ids=None):
    """Return unique email addresses for all staff and superusers."""
    qs = User.objects.filter(Q(is_staff=True) | Q(
        is_superuser=True)).exclude(email="")
    if exclude_user_ids:
        qs = qs.exclude(pk__in=exclude_user_ids)
    emails = qs.values_list("email", flat=True)
    return list(set(emails))


def _notify_staff(subject, message, exclude_user_ids=None):
    """Send an email notification to all staff and superusers."""
    recipients = _collect_staff_recipients(exclude_user_ids)
    if not recipients:
        return
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipients)


@receiver(post_save, sender=User, dispatch_uid="accounts_user_created_notify")
def notify_staff_user_registered(sender, instance, created, **kwargs):
    """Notify staff when a new user account is created."""
    if not created:
        return
    subject = f"New user registered: {instance.username}"
    lines = [
        "A new user has registered on Game Abyss.",
        f"Username: {instance.username}",
    ]
    if instance.email:
        lines.append(f"Email: {instance.email}")
    if instance.get_full_name():
        lines.append(f"Name: {instance.get_full_name()}")
    message = "\n".join(lines)
    _notify_staff(subject, message, exclude_user_ids=[instance.pk])


@receiver(post_delete, sender=User, dispatch_uid="accounts_user_deleted_notify")
def notify_staff_user_deleted(sender, instance, **kwargs):
    """Notify staff when a user account is deleted."""
    subject = f"User account deleted: {instance.username}"
    lines = [
        "A user account has been deleted from Game Abyss.",
        f"Username: {instance.username}",
    ]
    if instance.email:
        lines.append(f"Email: {instance.email}")
    message = "\n".join(lines)
    _notify_staff(subject, message)
