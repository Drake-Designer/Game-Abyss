"""
Signals for the blog app.

- on_post_created: notify superadmins when a new post is created
- on_comment_created: notify superadmins when a new comment is created
- on_comment_report_created: notify staff when a comment is reported
"""

from __future__ import annotations

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .emails import (
    notify_superadmins_new_post,
    notify_staff_comment_report,
    notify_superadmins_new_comment,
)
from .models import BlogPost, Comment, CommentReport


@receiver(post_save, sender=BlogPost, dispatch_uid="blog_post_created_notify")
def on_post_created(sender, instance: BlogPost, created: bool, **kwargs):
    """Send notification to superadmins when a new post is submitted."""
    if not created:
        return
    transaction.on_commit(lambda: notify_superadmins_new_post(instance))


@receiver(post_save, sender=Comment, dispatch_uid="blog_comment_created_notify")
def on_comment_created(sender, instance: Comment, created: bool, **kwargs):
    """Send notification to superadmins when a new comment is submitted."""
    if not created:
        return
    transaction.on_commit(lambda: notify_superadmins_new_comment(instance))


@receiver(
    post_save,
    sender=CommentReport,
    dispatch_uid="blog_comment_report_created_notify",
)
def on_comment_report_created(sender, instance: CommentReport, created: bool, **kwargs):
    """Send notification to staff when a comment is reported."""
    if not created:
        return
    transaction.on_commit(lambda: notify_staff_comment_report(instance))
