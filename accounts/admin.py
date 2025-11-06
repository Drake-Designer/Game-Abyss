"""Admin configuration for the accounts app."""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import UserProfile

User = get_user_model()


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile."""

    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"

    fields = (
        "avatar_preview",
        "avatar",
        "date_of_birth",
        "bio",
        "favorite_games",
        "favorite_genres",
    )
    readonly_fields = ("avatar_preview",)

    def avatar_preview(self, obj):
        """Display a preview of the avatar image."""
        if obj and obj.avatar:
            try:
                return format_html(
                    '<img src="{}" style="max-height: 150px; '
                    'max-width: 150px; border-radius: 8px;" />',
                    obj.avatar.url
                )
            except (ValueError, FileNotFoundError):
                return "Avatar not available"
        return "No avatar uploaded"
    avatar_preview.short_description = "Current Avatar"


class CustomUserAdmin(BaseUserAdmin):
    """Custom User admin with UserProfile inline."""

    inlines = (UserProfileInline,)

    # Fields to display in the user list
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
        "date_joined",
    )

    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "date_joined",
    )

    # Fields available in the user edit form
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Personal info",
            {"fields": ("first_name", "last_name", "email")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Important dates",
            {"fields": ("last_login", "date_joined")},
        ),
    )

    # Fields for adding a new user
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                ),
            },
        ),
    )

    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("-date_joined",)


# Unregister the default User admin if it exists
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

# Register the custom User admin with UserProfile inline
admin.site.register(User, CustomUserAdmin)
