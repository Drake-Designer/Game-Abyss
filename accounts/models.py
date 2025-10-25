from django.conf import settings
from django.db import models
from django.templatetags.static import static


class UserProfile(models.Model):
    """Additional profile data for a user."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    date_of_birth = models.DateField(blank=True, null=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(
        "Profile avatar",
        upload_to="avatars/",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"Profile for {self.user}" if self.user_id else "Profile"

    @property
    def has_avatar(self):
        """Return True when a custom avatar is uploaded."""
        return bool(self.avatar)

    def get_avatar_url(self):
        """Return the avatar URL or a static fallback image."""
        if self.avatar:
            return self.avatar.url
        return static("images/default-avatar.png")
