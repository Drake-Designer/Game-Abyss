# ============================================================
# *** ACCOUNTS APP CONFIGURATION ***
# ============================================================

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Configuration class for the Accounts app."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self) -> None:  # pragma: no cover
        """Import signals when the app is ready."""
        from . import signals  # pylint: disable=import-outside-toplevel, unused-import
