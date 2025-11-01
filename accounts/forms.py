# ============================================================
# *** ACCOUNTS FORMS: ProfileForm ***
# ============================================================

"""Forms for editing user profiles and associated user fields."""

from allauth.account.models import EmailAddress
from django import forms
from django.contrib.auth import get_user_model

from .models import UserProfile


class ProfileForm(forms.ModelForm):
    """
    Profile edit form combining:
    - User fields: first_name, last_name, email
    - Profile fields: avatar, date_of_birth, bio, favorite_games, favorite_genres
    """

    # User model fields (overridden for validation and initial values).
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = UserProfile
        fields = [
            "avatar",
            "date_of_birth",
            "bio",
            "favorite_games",
            "favorite_genres",
        ]
        widgets = {
            "avatar": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "date_of_birth": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "bio": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "favorite_games": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "favorite_genres": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        """Initialize the form with the current user context."""
        self.user = kwargs.pop("user", None)
        if self.user is None:
            raise ValueError("ProfileForm requires a 'user' keyword argument.")
        super().__init__(*args, **kwargs)

        self.fields["first_name"].initial = self.user.first_name
        self.fields["last_name"].initial = self.user.last_name
        self.fields["email"].initial = self.user.email
        self._initial_email = self._normalize_email(self.user.email)
        self.email_changed = False
        self.new_email = self._initial_email

    @staticmethod
    def _normalize_email(email: str | None) -> str:
        """Normalize email to lowercase and strip whitespace."""
        return str(email).strip().lower() if email else ""

    def clean_email(self):
        """Ensure the email is unique across User and EmailAddress tables."""
        email = self.cleaned_data.get("email")
        if not email:
            return ""
        email = self._normalize_email(email)
        user_model = get_user_model()

        if user_model.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError(
                "This email address is already in use.")
        if EmailAddress.objects.filter(email__iexact=email).exclude(user=self.user).exists():
            raise forms.ValidationError(
                "This email address is already in use.")
        return email

    def clean_favorite_games(self):
        """Strip leading and trailing spaces from favorite_games field."""
        return self.cleaned_data.get("favorite_games", "").strip()

    def clean_favorite_genres(self):
        """Strip leading and trailing spaces from favorite_genres field."""
        return self.cleaned_data.get("favorite_genres", "").strip()

    def save(self, commit: bool = True):
        """
        Save profile and synchronize linked User fields
        (first_name, last_name, email).
        """
        profile: UserProfile = super().save(commit=False)
        profile.user = self.user

        user_model = get_user_model()
        if isinstance(self.user, user_model):
            # Sync user first and last name.
            self.user.first_name = self.cleaned_data.get(
                "first_name", "") or ""
            self.user.last_name = self.cleaned_data.get("last_name", "") or ""
            update_fields = ["first_name", "last_name"]

            # Handle email changes.
            new_email = self.cleaned_data.get("email", "") or ""
            self.new_email = self._normalize_email(new_email)
            self.email_changed = self.new_email != self._initial_email

            if self.email_changed:
                self.user.email = self.new_email
                update_fields.append("email")

            if commit:
                self.user.save(update_fields=update_fields)

        if commit:
            profile.save()

        return profile
