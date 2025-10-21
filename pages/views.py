from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.views import View
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .forms import ContactForm


class HomeView(TemplateView):
    """Homepage view"""
    template_name = 'pages/home.html'


class AboutView(TemplateView):
    """About page view"""
    template_name = 'pages/about.html'


class ContactView(View):
    """Contact page view with form handling"""
    template_name = 'pages/contact.html'
    form_class = ContactForm

    def get(self, request):
        """Display contact form"""
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        """Handle contact form submission"""
        form = self.form_class(request.POST)

        if form.is_valid():
            # Get cleaned data
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']

            # Prepare email content
            email_subject = f"[Game Abyss Contact] {subject}"
            email_message = f"""
New contact form submission from Game Abyss:

From: {name} <{email}>
Subject: {subject}

Message:
{message}

---
This email was sent from the Game Abyss contact form.
Reply directly to this email to respond to {name}.
            """

            try:
                # Send email
                send_mail(
                    subject=email_subject,
                    message=email_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    # Send to yourself
                    recipient_list=[settings.DEFAULT_FROM_EMAIL],
                    fail_silently=False,
                )

                messages.success(
                    request,
                    f"Thanks {name}! Your message has been sent. We'll get back to you soon! 🎮"
                )
                return redirect('pages:contact')

            except Exception as e:
                # Log the actual error for debugging
                print(f"Email error: {str(e)}")
                messages.error(
                    request,
                    f"Oops! Something went wrong sending your message. Please try again later."
                )
                return render(request, self.template_name, {'form': form})

        # Form is invalid
        messages.error(
            request,
            "Please fix the errors below."
        )
        return render(request, self.template_name, {'form': form})
