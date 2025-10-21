from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('new/', views.new_post, name='new'),
]
