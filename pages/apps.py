# ============================================================
#   *** PAGES: App Config ***
# ============================================================

"""Configuration for the Pages app."""

from django.apps import AppConfig


class PagesConfig(AppConfig):
    """App settings and metadata for the Pages app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "pages"
