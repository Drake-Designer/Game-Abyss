from django.apps import AppConfig

"""
Blog app configuration.

Defines the application config used by Django to register the blog app.
"""


class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "blog"

    def ready(self):
        """
        Import signal handlers when the app is ready.
        Keeps it safe if signals.py is missing during early setup.
        """
        try:
            import blog.signals  # noqa: F401
        except ImportError:
            # No signals defined yet, safe to ignore
            pass
