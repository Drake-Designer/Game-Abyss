from django.apps import AppConfig


"""Pages app configuration.

Simple app config for the pages app (flat, static pages).
"""


class PagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pages'
