from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.views import View
from django.contrib import messages

from .forms import HelpRequestForm
from .models import HelpRequest

from blog.models import BlogPost
from gallery.models import GalleryImage  # NEW

HOME_FEATURED_POST_LIMIT = 6
HOME_FEATURED_GALLERY_LIMIT = 10  # NEW
HOME_OTHER_POSTS_PER_PAGE = 6


class HomeView(TemplateView):
    """Render the homepage."""
    template_name = 'pages/home.html'

    def get_context_data(self, **kwargs):
        """Include the featured posts grid and hero gallery images."""
        context = super().get_context_data(**kwargs)
        context['featured_posts'] = (
            BlogPost.objects.filter(
                featured=True,
                status=BlogPost.STATUS_APPROVED,
            )
            .select_related('author')
            .order_by('-published_at', '-updated_at')[:HOME_FEATURED_POST_LIMIT]
        )

        other_posts_qs = (
            BlogPost.objects.filter(
                featured=False,
                status=BlogPost.STATUS_APPROVED,
            )
            .select_related('author')
            .order_by('-published_at', '-updated_at')
        )
        page_number = self.request.GET.get('page')
        paginator = Paginator(other_posts_qs, HOME_OTHER_POSTS_PER_PAGE)
        context['other_posts_page'] = paginator.get_page(page_number)

        # NEW: featured & approved images for the hero carousel
        context['hero_gallery_images'] = (
            GalleryImage.objects.featured()
            .select_related('uploaded_by')[:HOME_FEATURED_GALLERY_LIMIT]
        )
        return context


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
