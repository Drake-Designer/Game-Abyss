from django.conf import settings
from django.db import models
from django.utils import timezone


class GalleryImageQuerySet(models.QuerySet):
    """Custom queryset with helpers for gallery moderation states."""

    def approved(self):
        return self.filter(status=self.model.Status.APPROVED)

    def featured(self):
        return (
            self.approved()
            .filter(is_featured=True)
            .order_by(models.F("featured_at").desc(nulls_last=True), "-created_at")
        )


class GalleryImage(models.Model):
    """Single image entry for the community gallery."""

    class Status(models.TextChoices):
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
        base = self.title or self.image.name
        return f"{base} ({self.get_status_display()})"

    def mark_featured(self):
        """Ensure featured timestamp stays in sync."""
        if self.is_featured and self.status != self.Status.APPROVED:
            self.status = self.Status.APPROVED
        if self.is_featured and not self.featured_at:
            self.featured_at = timezone.now()
        elif not self.is_featured:
            self.featured_at = None

    def save(self, *args, **kwargs):
        self.mark_featured()
        super().save(*args, **kwargs)
