from django.conf import settings
from django.db import models
from django.templatetags.static import static


class UserProfile(models.Model):
    """Extra profile data."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    date_of_birth = models.DateField(blank=True, null=True)
    bio = models.TextField(blank=True)

    favorite_games = models.TextField(
        blank=True,
        help_text="Favorite games separated by commas.",
    )
    favorite_genres = models.TextField(
        blank=True,
        help_text="Favorite genres separated by commas.",
    )

    avatar = models.ImageField(
        "Profile avatar",
        upload_to="avatars/",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self) -> str:
        return f"Profile for {self.user}" if self.user_id else "Profile"

    @property
    def has_avatar(self) -> bool:
        """True if a custom avatar exists."""
        return bool(self.avatar)

    def get_avatar_url(self) -> str:
        """Return avatar URL or a static fallback if missing or broken."""
        if self.avatar:
            try:
                return self.avatar.url
            except Exception:
                pass
        return static("images/default-avatar.png")
