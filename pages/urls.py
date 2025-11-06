# ============================================================
#    *** PAGES: URLs ***
# ============================================================

"""Define URL routes for the Pages app."""

from django.urls import path
from .views import HomeView, AboutView, ContactView, HomePostsPartialView

app_name = "pages"  # pylint: disable=invalid-name

urlpatterns = [
    # Home page
    path("", HomeView.as_view(), name="home"),
    path("home/posts/", HomePostsPartialView.as_view(), name="home_posts_partial"),

    # About page
    path("about/", AboutView.as_view(), name="about"),

    # Contact page
    path("contact/", ContactView.as_view(), name="contact"),
]
