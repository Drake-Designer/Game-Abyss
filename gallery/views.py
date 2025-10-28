# ============================================================
#   *** GALLERY: Views ***
# ============================================================

"""Define views for the gallery app."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from .forms import GalleryImageForm
from .models import GalleryImage


# ============================================================
#   *** GALLERY: Views: List View ***
# ============================================================


class GalleryListView(ListView):
    """Public gallery listing of approved images."""

    model = GalleryImage
    template_name = "gallery/list.html"
    context_object_name = "images"

    def get_queryset(self):
        """Return approved gallery images ordered by creation date."""
        return (
            GalleryImage.objects.approved()
            .select_related("uploaded_by")
            .order_by("-created_at")
        )


# ============================================================
#   *** GALLERY: Views: Upload View ***
# ============================================================


class GalleryUploadView(LoginRequiredMixin, CreateView):
    """Allow authenticated users to upload their images."""

    model = GalleryImage
    form_class = GalleryImageForm
    template_name = "gallery/upload.html"
    success_url = reverse_lazy("gallery:list")

    def form_valid(self, form):
        """Handle saving of uploaded images with moderation logic."""
        gallery_image = form.save(commit=False)
        gallery_image.uploaded_by = self.request.user

        if self.request.user.is_staff or self.request.user.is_superuser:
            gallery_image.status = GalleryImage.Status.APPROVED
            messages.success(
                self.request,
                "Your image has been uploaded and approved.",
            )
        else:
            gallery_image.status = GalleryImage.Status.PENDING
            messages.success(
                self.request,
                "Your image has been uploaded and is pending approval.",
            )

        gallery_image.save()
        self.object = gallery_image
        return HttpResponseRedirect(self.get_success_url())
