from django.shortcuts import render
from django.views.generic import TemplateView


class HomeView(TemplateView):
    """Homepage view"""
    template_name = 'pages/home.html'


class AboutView(TemplateView):
    """About page view"""
    template_name = 'pages/about.html'


class ContactView(TemplateView):
    """Contact page view"""
    template_name = 'pages/contact.html'
