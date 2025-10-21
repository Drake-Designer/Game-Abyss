from django.apps import AppConfig


"""Blog app configuration.

Defines the application config used by Django to register the blog app.
"""


class BlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'
