from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.post_list, name='index'),
    path('new/', views.new_post, name='new'),
    path('<int:year>/<int:month>/<int:day>/<slug:slug>/',
         views.post_detail, name='detail'),
]
