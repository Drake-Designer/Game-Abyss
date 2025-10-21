from django import forms


class ContactForm(forms.Form):
    """Contact form for sending messages"""

    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your name',
            'id': 'id_name'
        }),
        label='Name'
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com',
            'id': 'id_email'
        }),
        label='Email'
    )

    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': "What's this about?",
            'id': 'id_subject'
        }),
        label='Subject'
    )

    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Tell us more...',
            'rows': 6,
            'id': 'id_message'
        }),
        label='Message'
    )
