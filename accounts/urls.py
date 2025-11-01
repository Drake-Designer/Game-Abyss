# ============================================================
# *** ACCOUNTS URLS: URL configuration for the accounts app ***
# ============================================================

"""
URL configuration for the accounts app.
Defines all routes for user profiles, authentication helpers,
and staff moderation dashboards.
"""

from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    # ========================================================
    # User profile management
    # ========================================================
    path("profile/", views.my_profile_redirect, name="my_profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("profile/delete/", views.profile_delete, name="profile_delete"),
    path(
        "password/change/",
        views.VerifiedEmailPasswordChangeView.as_view(),
        name="account_change_password",
    ),

    # ========================================================
    # Staff dashboards and moderation tools
    # ========================================================
    path("staff/", views.staff_dashboard, name="staff_dashboard"),
    path("staff/moderation/posts/", views.staff_pending_posts,
         name="staff_pending_posts"),
    path("staff/moderation/comments/", views.staff_pending_comments,
         name="staff_pending_comments"),
    path("staff/moderation/reports/", views.staff_reports, name="staff_reports"),
    path("staff/help/requests/", views.staff_help_requests,
         name="staff_help_requests"),
    path("staff/users/", views.staff_user_search, name="staff_user_search"),
    path("staff/featured/", views.staff_featured_manager,
         name="staff_featured_manager"),
    path("staff/content/", views.staff_content_search,
         name="staff_content_search"),
    path("staff/view-as/", views.staff_view_as_user, name="staff_view_as_user"),

    # ========================================================
    # Public profile routes
    # ========================================================
    path("u/<str:username>/", views.profile, name="profile"),
]
