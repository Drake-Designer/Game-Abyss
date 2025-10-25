"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth system (django-allauth)
    path('accounts/', include('allauth.urls')),

    # Custom user profiles
    path('user/', include(('accounts.urls', 'accounts'), namespace='accounts')),

    # Pages app (home, about, contact)
    path('', include('pages.urls')),

    # Blog app
    path('blog/', include('blog.urls', namespace='blog')),
]

# Custom error handlers
handler403 = "core.views.permission_denied_view"
