# /* ============================================================
#    *** BLOG: AppConfig ***
#    ============================================================ */
"""Define configuration for the blog app."""

# /* ============================================================
#    *** BLOG: AppConfig: Imports ***
#    ============================================================ */
from importlib import import_module
from django.apps import AppConfig


# /* ============================================================
#    *** BLOG: AppConfig: Main Class ***
#    ============================================================ */
class BlogConfig(AppConfig):
    """Configure the blog application."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "blog"

    def ready(self) -> None:
        """
        Import signal handlers when the app is ready.
        Kept inside ready() to avoid import side effects at import time.
        """
        try:
            import_module("blog.signals")  # noqa: F401  imported for side effects
        except ImportError:
            # Signals are optional during early setup or testing
            pass
