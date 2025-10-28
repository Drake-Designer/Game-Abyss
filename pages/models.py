# ============================================================
#    *** PAGES: Models ***
# ============================================================

"""Define models for the Pages app."""

from django.contrib.auth import get_user_model
from django.db import models


# ============================================================
#    *** PAGES: Models: User Reference ***
# ============================================================

User = get_user_model()


# ============================================================
#    *** PAGES: Models: Help Request ***
# ============================================================


class HelpRequest(models.Model):
    """A support/help request created by a user."""

    # --- Status choices ---
    STATUS_OPEN = "open"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_RESOLVED = "resolved"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_IN_PROGRESS, "In progress"),
        (STATUS_RESOLVED, "Resolved"),
    ]

    # --- Priority choices ---
    PRIORITY_LOW = "low"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_HIGH = "high"
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "Low"),
        (PRIORITY_MEDIUM, "Medium"),
        (PRIORITY_HIGH, "High"),
    ]

    # --- Fields ---
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="help_requests",
    )
    name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_OPEN,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta options for HelpRequest."""

        ordering = ["-created_at"]
        verbose_name = "Help request"
        verbose_name_plural = "Help requests"

    def __str__(self):
        """Return readable representation of the help request."""
        identifier = self.subject or "Help request"
        return f"{identifier} ({self.get_status_display()})"
