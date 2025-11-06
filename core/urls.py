"""URL configuration for Game Abyss."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from accounts.views import VerifiedEmailPasswordChangeView
from core import views as core_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "summernote/upload_attachment/",
        core_views.summernote_attachment_disabled,
        name="django_summernote-upload_attachment",
    ),
    path("summernote/", include("django_summernote.urls")),

    # Auth
    path(
        "accounts/password/change/",
        VerifiedEmailPasswordChangeView.as_view(),
        name="account_change_password",
    ),
    path("accounts/", include("allauth.urls")),

    # App routes
    path("", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("", include("pages.urls")),
    path("blog/", include(("blog.urls", "blog"), namespace="blog")),
    path("gallery/", include(("gallery.urls", "gallery"), namespace="gallery")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

# Django requires these names exactly
handler403 = core_views.permission_denied_view  # pylint: disable=invalid-name
handler404 = core_views.page_not_found_view     # pylint: disable=invalid-name
handler500 = core_views.server_error_view       # pylint: disable=invalid-name
