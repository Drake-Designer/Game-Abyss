# ============================================================
#   *** GALLERY: URLs ***
# ============================================================

"""Define URL routes for the gallery app."""

from django.urls import path

from .views import (
    GalleryImageDeleteView,
    GalleryListView,
    GalleryMyImagesView,
    GalleryUploadView,
)

app_name = "gallery"

urlpatterns = [
    path("", GalleryListView.as_view(), name="list"),
    path("upload/", GalleryUploadView.as_view(), name="upload"),
    path("mine/", GalleryMyImagesView.as_view(), name="my_images"),
    path("<int:pk>/delete/", GalleryImageDeleteView.as_view(), name="delete"),
]
