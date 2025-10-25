"""Forms for the gallery app."""

from django import forms
from django.core.exceptions import ValidationError

from .models import GalleryImage


class GalleryImageForm(forms.ModelForm):
    """Upload form with basic safety validation for community images."""

    MAX_UPLOAD_SIZE_MB = 10
    ALLOWED_CONTENT_TYPES = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
    }

    class Meta:
        model = GalleryImage
        fields = ["image", "title", "caption"]
        widgets = {
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "title": forms.TextInput(
                attrs={"class": "form-control",
                       "placeholder": "Optional title"}
            ),
            "caption": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Add a short caption (optional)",
                    "rows": 4,
                }
            ),
        }
        help_texts = {
            "image": "Upload a JPEG, PNG, WEBP, or GIF up to 10 MB.",
        }

    def clean_image(self):
        """Ensure the uploaded file is an image and within the size limit."""
        image = self.cleaned_data.get("image")
        if not image:
            raise ValidationError("Please choose an image to upload.")

        # Try to detect content type from upload or underlying file
        content_type = getattr(image, "content_type", None)
        if not content_type:
            content_type = getattr(
                getattr(image, "file", None), "content_type", None)

        if content_type and content_type not in self.ALLOWED_CONTENT_TYPES:
            raise ValidationError(
                "Only JPEG, PNG, WEBP, or GIF files are supported.")
        if not content_type:
            # Fallback check by extension
            valid_ext = (".jpg", ".jpeg", ".png", ".webp", ".gif")
            if image.name and not image.name.lower().endswith(valid_ext):
                raise ValidationError(
                    "Unsupported file extension for the gallery upload.")

        max_bytes = self.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if image.size > max_bytes:
            raise ValidationError(
                f"Please upload files smaller than {self.MAX_UPLOAD_SIZE_MB} MB."
            )

        return image
