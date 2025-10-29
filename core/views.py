"""
Core-level views for custom error handling and other shared responses.
"""

from django.shortcuts import render


def permission_denied_view(request, exception=None):
    """Custom 403 Forbidden handler."""
    return render(request, "errors/403.html", status=403)


def page_not_found_view(request, exception):
    """Custom 404 Not Found handler."""
    return render(request, "errors/404.html", status=404)


def server_error_view(request):
    """Custom 500 Server Error handler."""
    return render(request, "errors/500.html", status=500)
