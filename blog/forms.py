from django import forms
from .models import BlogPost


class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'excerpt', 'body', 'image', 'tags', 'status']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 8}),
            'excerpt': forms.Textarea(attrs={'rows': 2}),
            'tags': forms.TextInput(attrs={'placeholder': 'tag1, tag2, ...'}),
        }
