# ============================================================
#    *** PAGES: Views ***
# ============================================================

"""Render pages views including home, about, and contact."""

from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.views import View
from django.contrib import messages

from .forms import HelpRequestForm
from .models import HelpRequest

from blog.models import BlogPost
from gallery.models import GalleryImage

# Homepage constants
HOME_FEATURED_POST_LIMIT = 6
HOME_FEATURED_GALLERY_LIMIT = 10
HOME_OTHER_POSTS_PER_PAGE = 6


# ============================================================
#    *** PAGES: Views: Home ***
# ============================================================


class HomeView(TemplateView):
    """Render the homepage with featured posts and gallery highlights."""
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        """Add featured posts, other posts, and gallery images to context."""
        context = super().get_context_data(**kwargs)

        # Featured posts
        featured_qs = (
            BlogPost.objects.filter(
                featured=True,
                status=BlogPost.STATUS_APPROVED,
            )
            .select_related("author")
            .order_by("-published_at", "-updated_at")
        )
        featured_posts = list(featured_qs[:HOME_FEATURED_POST_LIMIT])
        context["featured_posts"] = featured_posts

        # Latest posts section
        latest_posts_qs = (
            BlogPost.objects.filter(
                featured=False,
                status=BlogPost.STATUS_APPROVED,
            )
            .select_related("author")
            .order_by("-published_at", "-updated_at")
        )

        # Paginate latest posts
        page_number = self.request.GET.get("page")
        paginator = Paginator(latest_posts_qs, HOME_OTHER_POSTS_PER_PAGE)
        context["latest_posts_page"] = paginator.get_page(page_number)

        # Hero carousel images
        context["hero_gallery_images"] = (
            GalleryImage.objects.featured()
            .select_related("uploaded_by")[:HOME_FEATURED_GALLERY_LIMIT]
        )

        return context


# ============================================================
#    *** PAGES: Views: About ***
# ============================================================


class AboutView(TemplateView):
    """Simple about page."""
    template_name = "pages/about.html"


# ============================================================
#    *** PAGES: Views: Contact ***
# ============================================================


class ContactView(View):
    """Contact page backed by the HelpRequest model."""

    template_name = "pages/contact.html"
    form_class = HelpRequestForm

    def get_initial(self, request):
        """Return default values for the help request form."""
        initial = {"priority": HelpRequest.PRIORITY_MEDIUM}
        if request.user.is_authenticated:
            initial.update({
                "name": request.user.get_full_name() or request.user.get_username(),
                "email": request.user.email,
            })
        return initial

    def get(self, request):
        """Render the form with default values."""
        form = self.form_class(initial=self.get_initial(request))
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        """Handle form submission and create a HelpRequest entry."""
        form = self.form_class(request.POST)

        if form.is_valid():
            help_request = form.save(commit=False)

            # Auto-fill user info if authenticated
            if request.user.is_authenticated:
                help_request.user = request.user
                if not help_request.name:
                    help_request.name = request.user.get_full_name() or request.user.get_username()
                if not help_request.email:
                    help_request.email = request.user.email

            # Ensure defaults for status and priority
            help_request.status = help_request.status or HelpRequest.STATUS_OPEN
            help_request.priority = help_request.priority or HelpRequest.PRIORITY_MEDIUM
            help_request.save()

            messages.success(
                request,
                "Thanks for reaching out! Your help request has been submitted successfully."
            )
            return redirect("pages:contact")

        # Show error message if form is invalid
        messages.error(
            request,
            "We couldn't send your request. Please review the errors below and try again."
        )
        return render(request, self.template_name, {"form": form})
