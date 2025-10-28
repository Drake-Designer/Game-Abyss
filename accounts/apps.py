# ============================================================
# *** ACCOUNTS APP CONFIGURATION ***
# ============================================================

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    # Default primary key field type.
    default_auto_field = "django.db.models.BigAutoField"
    # App name reference.
    name = "accounts"

    def ready(self) -> None:  # pragma: no cover - signal registration
        # Import signals to ensure they are registered when the app is ready.
        from . import signals  # noqa: F401
