# ============================================================
#    *** PAGES: Forms ***
# ============================================================

"""Define pages app forms."""

# ============================================================
#    *** PAGES: Forms: Imports ***
# ============================================================

from django import forms

from .models import HelpRequest


# ============================================================
#    *** PAGES: Forms: Help Request Form ***
# ============================================================


class HelpRequestForm(forms.ModelForm):
    """Build a form for help requests."""

    class Meta:
        """Configure the help request form fields."""

        model = HelpRequest
        fields = [
            "name",
            "email",
            "subject",
            "message",
            "priority",
        ]
        labels = {
            "name": "Name",
            "email": "Email",
            "subject": "Subject",
            "message": "Description",
            "priority": "Priority",
        }
        help_texts = {
            "priority": "Choose how urgent your request is so our team can prioritise it.",
        }
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Your name",
                    "id": "id_name",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "your@email.com",
                    "id": "id_email",
                }
            ),
            "subject": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "What's this about?",
                    "id": "id_subject",
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Tell us more...",
                    "rows": 6,
                    "id": "id_message",
                }
            ),
            "priority": forms.Select(
                attrs={
                    "class": "form-select",
                    "id": "id_priority",
                }
            ),
        }
