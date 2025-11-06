"""
Core-level views for custom error handling and other shared responses.
"""

from typing import Optional

from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


def permission_denied_view(
    request: HttpRequest,
    exception: Optional[Exception] = None,
    **kwargs,
) -> HttpResponse:
    """Custom 403 Forbidden handler."""
    # pylint: disable=unused-argument
    return render(request, "errors/403.html", status=403)


def page_not_found_view(
    request: HttpRequest,
    exception: Optional[Exception] = None,
    **kwargs,
) -> HttpResponse:
    """Custom 404 Not Found handler."""
    # pylint: disable=unused-argument
    return render(request, "errors/404.html", status=404)


def server_error_view(request: HttpRequest) -> HttpResponse:
    """Custom 500 Server Error handler."""
    return render(request, "errors/500.html", status=500)


@csrf_exempt
def summernote_attachment_disabled(request: HttpRequest) -> HttpResponseForbidden:  # pylint: disable=unused-argument
    """Return a forbidden response for Summernote attachment uploads."""
    return HttpResponseForbidden("File uploads are disabled for this editor.")
