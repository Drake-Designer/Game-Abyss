# ============================================================
#    *** PAGES: Views ***
# ============================================================

"""Render pages views including home, about, and contact."""

from django.core.paginator import Paginator
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
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


def get_home_posts_queryset(*, featured):
    """Return the queryset for homepage posts filtered by featured flag."""
    return (
        BlogPost.objects.filter(
            featured=featured,
            status=BlogPost.STATUS_APPROVED,
        )
        .select_related("author")
        .order_by("-published_at", "-updated_at")
    )


# ============================================================
#    *** PAGES: Views: Home ***
# ============================================================

class HomeView(TemplateView):
    """Render the homepage with featured posts and gallery highlights."""
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        """Add featured posts, other posts, and gallery images to context."""
        context = super().get_context_data(**kwargs)

        # Featured posts section with pagination
        featured_qs = get_home_posts_queryset(featured=True)
        featured_page_number = self.request.GET.get("featured_page")
        featured_paginator = Paginator(featured_qs, HOME_FEATURED_POST_LIMIT)
        context["featured_posts_page"] = featured_paginator.get_page(
            featured_page_number)
        # Retro compat per i test esistenti
        context["featured_posts"] = list(
            context["featured_posts_page"].object_list)

        # Latest posts section with pagination
        latest_posts_qs = get_home_posts_queryset(featured=False)
        latest_page_number = self.request.GET.get(
            "latest_page") or self.request.GET.get("page")
        paginator = Paginator(latest_posts_qs, HOME_OTHER_POSTS_PER_PAGE)
        context["latest_posts_page"] = paginator.get_page(latest_page_number)

        # Hero carousel images
        context["hero_gallery_images"] = (
            GalleryImage.objects.featured()
            .select_related("uploaded_by")[:HOME_FEATURED_GALLERY_LIMIT]
        )

        return context


class HomePostsPartialView(View):
    """Return JSON payload with rendered posts and pagination for the homepage."""

    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        if request.headers.get("x-requested-with") != "XMLHttpRequest":
            return HttpResponseBadRequest("Invalid request.")

        section = request.GET.get("section")
        if section not in {"featured", "latest"}:
            return HttpResponseBadRequest("Unknown section.")

        page_number = request.GET.get("page")
        is_featured = section == "featured"
        queryset = get_home_posts_queryset(featured=is_featured)
        per_page = HOME_FEATURED_POST_LIMIT if is_featured else HOME_OTHER_POSTS_PER_PAGE
        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(page_number)

        context = {
            "posts_page": page_obj,
            "section": section,
            "page_param": "featured_page" if is_featured else "latest_page",
            "anchor_id": f"{section}-posts",
            "list_id": f"{section}-posts-list",
        }

        posts_html = render_to_string(
            "pages/partials/_home_posts_list.html",
            context,
            request=request,
        )
        pagination_html = render_to_string(
            "pages/partials/_home_posts_pagination.html",
            context,
            request=request,
        )

        return JsonResponse(
            {
                "posts_html": posts_html,
                "pagination_html": pagination_html,
                "page": page_obj.number,
            }
        )


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
