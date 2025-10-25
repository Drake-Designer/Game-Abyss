from django.conf import settings
from django.db import models

# Create your models here.


class UserProfile(models.Model):
    """Additional profile data for a user."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    date_of_birth = models.DateField(blank=True, null=True)
    bio = models.TextField(blank=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"Profile for {self.user}" if self.user_id else "Profile"
