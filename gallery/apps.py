# ============================================================
#   *** GALLERY: App Config ***
# ============================================================

"""Configuration for the Gallery app."""

from django.apps import AppConfig


class GalleryConfig(AppConfig):
    """App settings and metadata for the Gallery app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "gallery"
