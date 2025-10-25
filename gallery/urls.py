from django.urls import path

from .views import GalleryListView, GalleryUploadView

app_name = "gallery"

urlpatterns = [
    path("", GalleryListView.as_view(), name="list"),
    path("upload/", GalleryUploadView.as_view(), name="upload"),
]
