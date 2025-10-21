from django import forms
from .models import BlogPost


"""Forms for the blog app.

Contains a single ModelForm used by the admin and the front-end for
creating/editing BlogPost instances.
Provides a full-featured admin form and a restricted public submission form
for BlogPost instances.
"""


class BlogPostForm(forms.ModelForm):

    class Meta:
        model = BlogPost
        fields = ['author', 'title', 'excerpt',
                  'body', 'image', 'tags', 'status', 'is_approved']
        widgets = {
            'author': forms.Select(attrs={'class': 'form-select'}),
            'body': forms.Textarea(attrs={'rows': 8}),
            'excerpt': forms.Textarea(attrs={'rows': 2}),
            'tags': forms.TextInput(attrs={'placeholder': 'tag1, tag2, ...'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class PublicBlogPostForm(forms.ModelForm):
    """Form used on the public site. Keeps submissions as drafts awaiting review."""

    class Meta:
        model = BlogPost
        fields = ['title', 'excerpt', 'body', 'image', 'tags']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 8}),
            'excerpt': forms.Textarea(attrs={'rows': 2}),
            'tags': forms.TextInput(attrs={'placeholder': 'tag1, tag2, ...'}),
        }

    def save(self, commit=True):
        post = super().save(commit=False)
        post.status = 'draft'
        post.is_approved = False
        if commit:
            post.save()
        return post
