from django.shortcuts import render
from django.http import HttpResponse


def new_post(request):
    """Placeholder view for creating a new blog post."""
    if not request.user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)
    return HttpResponse('<h1>New Post - Placeholder</h1>')
