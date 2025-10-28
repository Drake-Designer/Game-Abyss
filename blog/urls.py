# /* ============================================================
#    *** BLOG: URLs ***
#    ============================================================ */
"""Define URL routes for the blog app."""

# /* ============================================================
#    *** BLOG: URLs: Imports ***
#    ============================================================ */
from django.urls import path

from . import views


# /* ============================================================
#    *** BLOG: URLs: Patterns ***
#    ============================================================ */

app_name = "blog"

urlpatterns = [
    # List approved posts on the homepage.
    path("", views.post_list, name="index"),

    # Filter posts by tag slug.
    path("tag/<slug:tag_slug>/", views.post_list, name="tag"),

    # Create a new post entry.
    path("new/", views.new_post, name="new"),

    # Manage post level actions.
    path("posts/<int:pk>/edit/", views.edit_post, name="edit_post"),
    path("posts/<int:pk>/delete/", views.delete_post, name="delete_post"),
    path("posts/<int:pk>/react/", views.react_to_post, name="react_post"),

    # Manage comment level actions.
    path("comments/<int:pk>/edit/", views.edit_comment, name="edit_comment"),
    path("comments/<int:pk>/react/", views.react_to_comment, name="react_comment"),
    path("comments/<int:pk>/report/", views.report_comment, name="report_comment"),
    path("comments/<int:pk>/delete/", views.delete_comment, name="delete_comment"),

    # Show a single post detail entry.
    path(
        "<int:year>/<int:month>/<int:day>/<slug:slug>/",
        views.post_detail,
        name="detail",
    ),
]

# Define custom forbidden handler.
handler403 = "core.views.permission_denied_view"
