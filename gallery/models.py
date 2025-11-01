# ============================================================
#   *** GALLERY: Models ***
# ============================================================

"""Define database models for the gallery app."""
# pylint: disable=too-many-ancestors


from django.conf import settings
from django.db import models
from django.utils import timezone


# ============================================================
#   *** GALLERY: Models: QuerySet ***
# ============================================================


class GalleryImageQuerySet(models.QuerySet):
    """Custom queryset with helpers for gallery moderation states."""

    def approved(self):
        """Return only approved images."""
        return self.filter(status=self.model.Status.APPROVED)

    def featured(self):
        """Return approved and featured images, ordered by featured_at and created_at."""
        return (
            self.approved()
            .filter(is_featured=True)
            .order_by(models.F("featured_at").desc(nulls_last=True), "-created_at")
        )


# ============================================================
#   *** GALLERY: Models: GalleryImage ***
# ============================================================


class GalleryImage(models.Model):  # pylint: disable=too-many-ancestors
    """Single image entry for the community gallery."""

    class Status(models.TextChoices):
        """Moderation states for gallery images."""
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    image = models.ImageField(upload_to="gallery/")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="gallery_images",
    )
    title = models.CharField(max_length=255, blank=True)
    caption = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    featured_at = models.DateTimeField(null=True, blank=True)

    objects = GalleryImageQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        """Return a readable representation of the image with status."""
        base = self.title or self.image.name
        return f"{base} ({self.get_status_display()})"

    def mark_featured(self):
        """Ensure featured timestamp and status stay in sync."""
        if self.is_featured and self.status != self.Status.APPROVED:
            self.status = self.Status.APPROVED
        if self.is_featured and not self.featured_at:
            self.featured_at = timezone.now()
        elif not self.is_featured:
            self.featured_at = None

    def save(self, *args, **kwargs):
        """Override save to enforce featured state consistency."""
        self.mark_featured()
        super().save(*args, **kwargs)
