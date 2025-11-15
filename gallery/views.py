# ============================================================
#   *** GALLERY: Views ***
# ============================================================

"""Define views for the gallery app."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView

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

    # Pre-dichiariamo l'attributo per Pylint
    object = None  # type: GalleryImage | None

    def form_valid(self, form):
        """Handle saving of uploaded images with moderation logic."""
        gallery_image = form.save(commit=False)
        gallery_image.uploaded_by = self.request.user

        if self.request.user.is_staff or self.request.user.is_superuser:
            gallery_image.status = GalleryImage.Status.APPROVED
            messages.success(
                self.request,
                "Live now — your image is visible.",
            )
        else:
            gallery_image.status = GalleryImage.Status.PENDING
            messages.success(
                self.request,
                "Thanks! Your image is awaiting a quick review.",
            )

        gallery_image.save()
        self.object = gallery_image
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        """Send users to their management dashboard after upload."""
        if self.request.user.is_authenticated:
            return reverse("gallery:my_images")
        return super().get_success_url()


class GalleryMyImagesView(LoginRequiredMixin, ListView):
    """List uploads that belong to the current user."""

    model = GalleryImage
    template_name = "gallery/my_images.html"
    context_object_name = "images"
    paginate_by = 9

    def get_queryset(self):
        """Return images scoped to the authenticated user."""
        return (
            GalleryImage.objects.filter(uploaded_by=self.request.user)
            .select_related("uploaded_by")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        """Add moderation stats for the user's uploads."""
        context = super().get_context_data(**kwargs)
        base_qs = GalleryImage.objects.filter(uploaded_by=self.request.user)
        context["status_counts"] = {
            "pending": base_qs.filter(status=GalleryImage.Status.PENDING).count(),
            "approved": base_qs.filter(status=GalleryImage.Status.APPROVED).count(),
            "rejected": base_qs.filter(status=GalleryImage.Status.REJECTED).count(),
        }
        return context


class GalleryImageDeleteView(
    LoginRequiredMixin, UserPassesTestMixin, DeleteView
):
    """Allow users (or staff) to delete gallery uploads."""

    model = GalleryImage
    template_name = "gallery/confirm_delete.html"
    context_object_name = "image"
    success_url = reverse_lazy("gallery:my_images")
    raise_exception = True

    def test_func(self):
        """Only owners or staff may delete the image."""
        image = self.get_object()
        user = self.request.user
        return user.is_staff or user.is_superuser or image.uploaded_by_id == user.id

    def get_success_url(self):
        """Respect next parameter when returning to previous page."""
        next_url = self.request.POST.get(
            "next") or self.request.GET.get("next")
        if next_url:
            return next_url
        return super().get_success_url()

    def delete(self, request, *args, **kwargs):
        """Delete the image and notify the user."""
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(request, "Image removed from your gallery.")
        return HttpResponseRedirect(success_url)
