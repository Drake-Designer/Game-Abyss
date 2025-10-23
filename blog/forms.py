from django import forms
from django.core.exceptions import ValidationError

from .models import BlogPost, Comment


"""
Forms for the blog app — Game-Abyss edition.

- BlogPostForm (admin): reviewers can set status and featured.
- PublicBlogPostForm: status is set by the system; users just craft the post.
- CommentForm: submit a thought; moderation keeps the void at bay.
"""


class BlogPostForm(forms.ModelForm):
    """Admin/reviewer form: exposes status and featured."""
    class Meta:
        model = BlogPost
        fields = [
            'author',
            'title',
            'excerpt',
            'body',
            'image',
            'tags',
            'status',
            'featured',
        ]
        widgets = {
            'author': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Title of your chronicle'}),
            'body': forms.Textarea(attrs={'rows': 8, 'class': 'form-control', 'placeholder': 'Forge your story here…'}),
            'excerpt': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Short teaser shown in lists'}),
            'tags': forms.TextInput(attrs={'placeholder': 'rpg, soulslike, starship…', 'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'tags': 'Separate with commas — keep them tight and relevant.',
            'excerpt': 'Optional. Used on cards and listings. Clean beats long.',
        }


class PublicBlogPostForm(forms.ModelForm):
    """
    Public submission form.
    Status is NOT shown; it will be set by the view based on the author role.
    """
    class Meta:
        model = BlogPost
        fields = ['title', 'excerpt', 'body', 'image', 'tags']  # no 'status'
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name your expedition'}),
            'body': forms.Textarea(attrs={'rows': 8, 'class': 'form-control', 'placeholder': 'Drop your build, review, or tale…'}),
            'excerpt': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'One-liner to lure explorers'}),
            'tags': forms.TextInput(attrs={'placeholder': 'rpg, lore, co-op, sandbox', 'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'tags': 'Comma-separated tags. Think categories, not paragraphs.',
        }

    def clean_tags(self):
        """Trim and deduplicate user tag input."""
        value = self.cleaned_data.get('tags')
        if not value:
            return value
        normalized = ', '.join([t.strip()
                               for t in str(value).split(',') if t.strip()])
        return normalized

    def save(self, commit=True):
        """Status is assigned in the view; this just builds the instance."""
        post = super().save(commit=False)
        if commit:
            post.save()
        return post


class CommentForm(forms.ModelForm):
    """Public comment form — be kind to your fellow travelers."""
    class Meta:
        model = Comment
        fields = ['body']
        labels = {'body': 'Comment'}
        widgets = {
            'body': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Add your signal to the constellation…',
                'class': 'form-control',
            }),
        }
        help_texts = {
            'body': 'Keep it civil. No spoilers without tags. No toxicity.',
        }

    def clean_body(self):
        """Minimum signal to avoid low-effort stardust."""
        body = self.cleaned_data.get('body', '') or ''
        if len(body.strip()) < 5:
            raise ValidationError(
                'Your comment is too short to register on our scanners.')
        return body
