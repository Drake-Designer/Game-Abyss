from django.urls import path
from . import views

app_name = 'blog'

"""
URL patterns for the blog app.

"""

urlpatterns = [
    path('', views.post_list, name='index'),
    path('new/', views.new_post, name='new'),

    # Reactions and reports
    path('posts/<int:pk>/react/', views.react_to_post, name='react_post'),
    path('comments/<int:pk>/react/', views.react_to_comment, name='react_comment'),
    path('comments/<int:pk>/report/', views.report_comment, name='report_comment'),

    # Post detail
    path('<int:year>/<int:month>/<int:day>/<slug:slug>/',
         views.post_detail, name='detail'),
]
