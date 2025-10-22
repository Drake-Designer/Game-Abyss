from django import forms
from django.core.exceptions import ValidationError

from .models import BlogPost, Comment


"""
Forms for the blog app.

- BlogPostForm: used in the admin site
- PublicBlogPostForm: used for public submissions, supports draft or publish
- CommentForm: used for public comment submission
"""


class BlogPostForm(forms.ModelForm):
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
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'rows': 8, 'class': 'form-control'}),
            'excerpt': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'tags': forms.TextInput(
                attrs={'placeholder': 'tag1, tag2, ...',
                       'class': 'form-control'}
            ),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'tags': 'Separate tags with commas.',
            'excerpt': 'A short summary shown in post listings.',
        }


class PublicBlogPostForm(forms.ModelForm):
    """Form used on the public site. Users can save drafts or publish."""

    class Meta:
        model = BlogPost
        fields = ['title', 'excerpt', 'body', 'image', 'tags', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'rows': 8, 'class': 'form-control'}),
            'excerpt': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'tags': forms.TextInput(
                attrs={'placeholder': 'tag1, tag2, ...',
                       'class': 'form-control'}
            ),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
        help_texts = {
            'tags': 'Separate tags with commas.',
            'status': 'Save as draft to continue later or publish immediately.',
        }

    def clean_tags(self):
        """Normalize tags string by trimming spaces and removing duplicates."""
        value = self.cleaned_data.get('tags')
        if not value:
            return value
        normalized = ', '.join([t.strip()
                               for t in str(value).split(',') if t.strip()])
        return normalized

    def save(self, commit=True):
        post = super().save(commit=False)
        if commit:
            post.save()
        return post


class CommentForm(forms.ModelForm):
    """Form used to submit a public comment on a blog post."""

    class Meta:
        model = Comment
        fields = ['body']
        labels = {'body': 'Comment'}
        widgets = {
            'body': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Share your thoughts…',
                'class': 'form-control',
            }),
        }
        help_texts = {
            'body': 'Keep a respectful tone. No spam.',
        }

    def clean_body(self):
        """Ensure that comments are not too short."""
        body = self.cleaned_data.get('body', '') or ''
        if len(body.strip()) < 5:
            raise ValidationError('The comment is too short.')
        return body
