from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.views import View
from django.contrib import messages

from .forms import HelpRequestForm
from .models import HelpRequest


class HomeView(TemplateView):
    """Render the homepage."""
    template_name = 'pages/home.html'


class AboutView(TemplateView):
    """Render the about page."""
    template_name = 'pages/about.html'


class ContactView(View):
    """Contact page backed by the HelpRequest model."""

    template_name = 'pages/contact.html'
    form_class = HelpRequestForm

    def get_initial(self, request):
        """Return default initial values for the form."""
        initial = {
            'priority': HelpRequest.PRIORITY_MEDIUM,
        }
        if request.user.is_authenticated:
            initial.update({
                'name': request.user.get_full_name() or request.user.get_username(),
                'email': request.user.email,
            })
        return initial

    def get(self, request):
        """Show the help request form."""
        form = self.form_class(initial=self.get_initial(request))
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        """Create a HelpRequest from the submitted data."""
        form = self.form_class(request.POST)

        if form.is_valid():
            help_request = form.save(commit=False)

            if request.user.is_authenticated:
                help_request.user = request.user
                # Auto-fill missing details from the authenticated user
                if not help_request.name:
                    help_request.name = request.user.get_full_name() or request.user.get_username()
                if not help_request.email:
                    help_request.email = request.user.email

            help_request.status = help_request.status or HelpRequest.STATUS_OPEN
            help_request.priority = help_request.priority or HelpRequest.PRIORITY_MEDIUM
            help_request.save()

            messages.success(
                request,
                "Thanks for reaching out! Your help request has been submitted successfully."
            )
            return redirect('pages:contact')

        messages.error(
            request,
            "We couldn't send your request. Please review the errors below and try again."
        )
        return render(request, self.template_name, {'form': form})
