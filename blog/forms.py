# /* ============================================================
#    *** BLOG: Forms ***
#    ============================================================ */
"""Define blog form classes."""

# /* ============================================================
#    *** BLOG: Forms: Imports ***
#    ============================================================ */
import re

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from .models import BlogPost, Comment


# /* ============================================================
#    *** BLOG: Forms: Administrative Forms ***
#    ============================================================ */


class BlogPostForm(forms.ModelForm):
    """Manage blog post submissions for staff."""
    class Meta:
        """Configure admin blog post form fields."""
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
            'tags': 'Separate with commas - keep them tight and relevant.',
            'excerpt': 'Optional. Used on cards and listings. Clean beats long.',
        }

    def clean_tags(self):
        """Normalize tag input for storage."""
        value = self.cleaned_data.get('tags')
        if not value:
            return ''
        return BlogPost.normalize_tags(value)


# /* ============================================================
#    *** BLOG: Forms: Public Post Form ***
#    ============================================================ */


class PublicBlogPostForm(forms.ModelForm):
    """Collect public blog post submissions."""
    class Meta:
        """Configure public blog post form fields."""
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
        """Normalize tags provided by public authors."""
        value = self.cleaned_data.get('tags')
        if not value:
            return ''
        return BlogPost.normalize_tags(value)

    def save(self, commit=True):
        """Save the public post without altering status."""
        post = super().save(commit=False)
        if commit:
            post.save()
        return post


# /* ============================================================
#    *** BLOG: Forms: Comment Form ***
#    ============================================================ */


class CommentForm(forms.ModelForm):
    """Collect public comment submissions."""
    class Meta:
        """Configure public comment form fields."""
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
        """Validate the comment body content."""
        body = self.cleaned_data.get('body', '') or ''
        if len(body.strip()) < 5:
            raise ValidationError(
                'Your comment is too short to register on our scanners.')

        lowered = body.lower()
        for word in getattr(settings, 'BLOG_COMMENT_BANNED_WORDS', []):
            if not word:
                continue
            pattern = r'\b{}\b'.format(re.escape(word))
            if re.search(pattern, lowered):
                raise ValidationError(
                    'Your comment contains language that is not allowed on Game-Abyss.'
                )

        max_links = getattr(settings, 'BLOG_COMMENT_MAX_LINKS', 2)
        if max_links >= 0:
            link_count = len(re.findall(
                r'https?://|www\.', body, flags=re.IGNORECASE))
            if link_count > max_links:
                raise ValidationError(
                    f'Please keep the number of links to {max_links} or fewer.'
                )
        return body
