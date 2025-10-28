# ============================================================
#   *** GALLERY: Admin ***
# ============================================================

"""Configure the gallery admin interface."""

from django.contrib import admin
from django.utils import timezone

from .models import GalleryImage


# ============================================================
#   *** GALLERY: Admin: Gallery Image Admin ***
# ============================================================


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    """Manage gallery images for staff users."""

    list_display = (
        "id",
        "preview_title",
        "uploaded_by",
        "status",
        "is_featured",
        "created_at",
        "featured_at",
    )
    list_filter = ("status", "is_featured", "created_at")
    search_fields = ("title", "caption",
                     "uploaded_by__username", "uploaded_by__email")
    actions = ("approve_images", "reject_images", "toggle_featured",)
    readonly_fields = ("created_at", "featured_at")
    ordering = ("-created_at",)

    def preview_title(self, obj):
        """Show the display title for the image."""
        return obj.title or obj.image.name

    preview_title.short_description = "Title"

    @admin.action(description="Approve selected images")
    def approve_images(self, request, queryset):
        """Approve selected gallery images."""
        featured_ids = list(
            queryset.filter(is_featured=True).values_list("pk", flat=True)
        )
        updated = queryset.update(status=GalleryImage.Status.APPROVED)
        if featured_ids:
            now = timezone.now()
            GalleryImage.objects.filter(
                pk__in=featured_ids).update(featured_at=now)
        self.message_user(request, f"{updated} image(s) approved.")

    @admin.action(description="Reject selected images")
    def reject_images(self, request, queryset):
        """Reject selected gallery images."""
        image_ids = list(queryset.values_list("pk", flat=True))
        updated = queryset.update(
            status=GalleryImage.Status.REJECTED, is_featured=False)
        if image_ids:
            GalleryImage.objects.filter(
                pk__in=image_ids).update(featured_at=None)
        self.message_user(request, f"{updated} image(s) rejected.")

    @admin.action(description="Toggle featured state")
    def toggle_featured(self, request, queryset):
        """Toggle the featured status for images."""
        toggled = 0
        for image in queryset:
            image.is_featured = not image.is_featured
            if image.is_featured:
                image.status = GalleryImage.Status.APPROVED
                image.featured_at = timezone.now()
            else:
                image.featured_at = None
            update_fields = ["status", "is_featured", "featured_at"]
            if hasattr(image, "updated_at"):
                update_fields.append("updated_at")
            image.save(update_fields=update_fields)
            toggled += 1
        self.message_user(
            request, f"Toggled featured flag for {toggled} image(s).")

    def save_model(self, request, obj, form, change):
        """Ensure featured metadata stays in sync."""
        if obj.is_featured and obj.status != GalleryImage.Status.APPROVED:
            obj.status = GalleryImage.Status.APPROVED
        if obj.is_featured:
            obj.featured_at = obj.featured_at or timezone.now()
        else:
            obj.featured_at = None
        super().save_model(request, obj, form, change)
