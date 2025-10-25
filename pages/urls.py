"""
URL configuration for the pages app.

"""

from django.urls import path
from .views import HomeView, AboutView, ContactView

app_name = "pages"

urlpatterns = [
    # Home page
    path("", HomeView.as_view(), name="home"),

    # About page
    path("about/", AboutView.as_view(), name="about"),

    # Contact page
    path("contact/", ContactView.as_view(), name="contact"),
]
