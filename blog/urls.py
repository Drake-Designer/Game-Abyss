from django.urls import path, include
from . import views

app_name = 'blog'

"""
URL patterns for the blog app.
"""

urlpatterns = [
    path('', views.post_list, name='index'),
    path('new/', views.new_post, name='new'),

    # Reactions and reports
    path('posts/<int:pk>/delete/', views.delete_post, name='delete_post'),
    path('posts/<int:pk>/react/', views.react_to_post, name='react_post'),
    path('comments/<int:pk>/react/', views.react_to_comment, name='react_comment'),
    path('comments/<int:pk>/report/', views.report_comment, name='report_comment'),
    path('comments/<int:pk>/delete/', views.delete_comment, name='delete_comment'),

    # Post detail
    path('<int:year>/<int:month>/<int:day>/<slug:slug>/',
         views.post_detail, name='detail'),
]

# Custom error handlers
handler403 = 'core.views.permission_denied_view'
