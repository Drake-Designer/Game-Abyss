"""
URL configuration for the blog app.
"""

from django.urls import path
from . import views

app_name = "blog"

urlpatterns = [
    # Blog homepage (list of approved posts)
    path("", views.post_list, name="index"),

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

    # Single post detail (with year/month/day/slug in URL)
    path(
        "<int:year>/<int:month>/<int:day>/<slug:slug>/",
        views.post_detail,
        name="detail",
    ),
]

# Custom error handler for forbidden actions
handler403 = "core.views.permission_denied_view"
