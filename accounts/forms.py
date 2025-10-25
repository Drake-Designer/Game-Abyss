from django import forms
from django.contrib.auth import get_user_model

from .models import UserProfile


class ProfileForm(forms.ModelForm):
    """
    A form that allows a user to edit their profile information.
    It combines User model fields (first_name, last_name)
    with additional fields stored in UserProfile (date_of_birth, bio, avatar).
    """

    # These belong to the main User model
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = UserProfile
        fields = ["avatar", "date_of_birth", "bio"]
        widgets = {
            "avatar": forms.ClearableFileInput(attrs={"class": "form-control"}),
            # date picker
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "bio": forms.Textarea(attrs={"rows": 4}),  # textarea with 4 rows
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["first_name"].initial = self.user.first_name
        self.fields["last_name"].initial = self.user.last_name

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.user = self.user
        User = get_user_model()
        if isinstance(self.user, User):
            self.user.first_name = self.cleaned_data.get("first_name", "")
            self.user.last_name = self.cleaned_data.get("last_name", "")
            if commit:
                self.user.save(update_fields=["first_name", "last_name"])
        if commit:
            profile.save()
        return profile
