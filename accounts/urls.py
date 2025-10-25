"""
URL configuration for the accounts app.

"""

from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    # Redirect logged-in user to their own profile
    path("profile/", views.my_profile_redirect, name="my_profile"),

    # Edit profile details (first name, last name, date of birth, bio)
    path("profile/edit/", views.profile_edit, name="profile_edit"),

    # Delete user profile + cascade delete posts and comments
    path("profile/delete/", views.profile_delete, name="profile_delete"),

    # Public profile by username
    path("profile/<str:username>/", views.profile, name="profile"),
]
