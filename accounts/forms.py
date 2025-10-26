from allauth.account.models import EmailAddress
from django import forms
from django.contrib.auth import get_user_model

from .models import UserProfile


class ProfileForm(forms.ModelForm):
    """
    A form that allows a user to edit their profile information.
    It combines User model fields (first_name, last_name, email)
    with additional fields stored in UserProfile (date_of_birth, bio, avatar).
    """

    # These belong to the main User model
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = UserProfile
        fields = ["avatar", "date_of_birth", "bio"]
        widgets = {
            "avatar": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "bio": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["first_name"].initial = self.user.first_name
        self.fields["last_name"].initial = self.user.last_name
        self.fields["email"].initial = self.user.email
        self._initial_email = self._normalize_email(self.user.email)
        self.email_changed = False
        self.new_email = self._initial_email

    @staticmethod
    def _normalize_email(email: str | None) -> str:
        if not email:
            return ""
        return str(email).strip().lower()

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            return ""

        email = self._normalize_email(email)
        User = get_user_model()
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError(
                "This email address is already in use.")

        if EmailAddress.objects.filter(email__iexact=email).exclude(user=self.user).exists():
            raise forms.ValidationError(
                "This email address is already in use.")

        return email

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.user = self.user
        User = get_user_model()
        if isinstance(self.user, User):
            self.user.first_name = self.cleaned_data.get("first_name", "")
            self.user.last_name = self.cleaned_data.get("last_name", "")
            user_update_fields = ["first_name", "last_name"]

            new_email = self.cleaned_data.get("email", "") or ""
            self.new_email = new_email
            self.email_changed = new_email != self._initial_email

            if self.email_changed:
                self.user.email = new_email
                user_update_fields.append("email")

            if commit:
                self.user.save(update_fields=user_update_fields)
        if commit:
            profile.save()
        return profile
