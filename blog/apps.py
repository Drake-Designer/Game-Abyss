# /* ============================================================
#    *** BLOG: AppConfig ***
#    ============================================================ */
"""Define configuration for the blog app."""

# /* ============================================================
#    *** BLOG: AppConfig: Imports ***
#    ============================================================ */
from django.apps import AppConfig


# /* ============================================================
#    *** BLOG: AppConfig: Main Class ***
#    ============================================================ */
class BlogConfig(AppConfig):
    """Configure the blog application."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "blog"

    def ready(self):
        """Import signal handlers when the app is ready."""
        try:
            import blog.signals  # noqa: F401
        except ImportError:
            # Safe to ignore if signals module is missing during setup
            pass
