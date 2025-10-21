from django import forms
from .models import BlogPost


"""Forms for the blog app.

Contains a single ModelForm used by the admin and the front-end for
creating/editing BlogPost instances.
"""


class BlogPostForm(forms.ModelForm):
    # explicit slug field to guarantee the form exposes it at runtime
    slug = forms.SlugField(required=False)

    class Meta:
        model = BlogPost
        fields = ['author', 'title', 'slug', 'excerpt',
                  'body', 'image', 'tags', 'status']
        widgets = {
            'author': forms.Select(attrs={
                'class': 'custom-admin-select',
                'style': 'background-color:#221f24;color:#ffffff;border:2px solid #d35400;border-radius:8px;padding:6px 8px;'
            }),
            'body': forms.Textarea(attrs={'rows': 8}),
            'excerpt': forms.Textarea(attrs={'rows': 2}),
            'tags': forms.TextInput(attrs={'placeholder': 'tag1, tag2, ...'}),
            'status': forms.Select(attrs={
                'class': 'custom-admin-select',
                'style': 'background-color:#221f24;color:#ffffff;border:2px solid #d35400;border-radius:8px;padding:6px 8px;'
            }),
        }
