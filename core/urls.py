"""
URL configuration for core project.

For more information see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication system (django-allauth)
    path('accounts/', include('allauth.urls')),

    # Custom user profiles
    path('user/', include(('accounts.urls', 'accounts'), namespace='accounts')),

    # Pages app (home, about, contact)
    path('', include('pages.urls')),

    # Blog app
    path('blog/', include('blog.urls', namespace='blog')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler403 = "core.views.permission_denied_view"
