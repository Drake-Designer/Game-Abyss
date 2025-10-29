from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from accounts.views import VerifiedEmailPasswordChangeView

urlpatterns = [
    path("admin/", admin.site.urls),

    path(
        "accounts/password/change/",
        VerifiedEmailPasswordChangeView.as_view(),
        name="account_change_password",
    ),
    path("accounts/", include("allauth.urls")),

    # Accounts alla root: il profilo pubblico è /u/<username>/
    path("", include(("accounts.urls", "accounts"), namespace="accounts")),

    path("", include("pages.urls")),
    path("blog/", include("blog.urls", namespace="blog")),
    path("gallery/", include("gallery.urls", namespace="gallery")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

handler403 = "core.views.permission_denied_view"
handler404 = "core.views.page_not_found_view"
handler500 = "core.views.server_error_view"
