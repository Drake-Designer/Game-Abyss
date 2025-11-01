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

# Django expects app_name to be lowercase; silence Pylint for naming rule
app_name = "blog"  # pylint: disable=invalid-name

urlpatterns = [
    # List approved posts on the homepage
    path("", views.post_list, name="index"),

    # Filter posts by tag slug
    path("tag/<slug:tag_slug>/", views.post_list, name="tag"),

    # Create a new post
    path("new/", views.new_post, name="new"),

    # Post actions
    path("posts/<int:pk>/edit/", views.edit_post, name="edit_post"),
    path("posts/<int:pk>/delete/", views.delete_post, name="delete_post"),
    path("posts/<int:pk>/react/", views.react_to_post, name="react_post"),

    # Comment actions
    path("comments/<int:pk>/edit/", views.edit_comment, name="edit_comment"),
    path("comments/<int:pk>/react/", views.react_to_comment, name="react_comment"),
    path("comments/<int:pk>/report/", views.report_comment, name="report_comment"),
    path("comments/<int:pk>/delete/", views.delete_comment, name="delete_comment"),

    # Single post detail
    path(
        "<int:year>/<int:month>/<int:day>/<slug:slug>/",
        views.post_detail,
        name="detail",
    ),
]

# Global error handlers should remain in core/urls.py, not here.
