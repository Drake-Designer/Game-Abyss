"""
Signals for the blog app.

- on_comment_created: notify superadmins when a new comment is created (pending)
- on_comment_report_created: notify staff when a comment is reported
"""

from __future__ import annotations

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .emails import (
    notify_staff_comment_report,
    notify_superadmins_new_comment,
)
from .models import Comment, CommentReport


@receiver(post_save, sender=Comment)
def on_comment_created(sender, instance: Comment, created: bool, **kwargs):
    """Send notification to superadmins when a new comment is submitted."""
    if not created:
        return
    # Delay sending until after DB transaction is committed
    transaction.on_commit(lambda: notify_superadmins_new_comment(instance))


@receiver(post_save, sender=CommentReport)
def on_comment_report_created(sender, instance: CommentReport, created: bool, **kwargs):
    """Send notification to staff when a comment is reported."""
    if not created:
        return
    transaction.on_commit(lambda: notify_staff_comment_report(instance))
