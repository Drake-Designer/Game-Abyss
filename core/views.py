"""
Core-level views for custom error handling and other shared responses.
"""

from django.shortcuts import render


def permission_denied_view(request, exception=None):
    """
    Custom 403 Forbidden handler.
    """
    return render(request, "errors/403.html", status=403)
