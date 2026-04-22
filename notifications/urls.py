from django.urls import path

from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='list'),
    path('read/<int:nid>/', views.mark_as_read, name='read'),
    path('read/all/', views.mark_all_read, name='read_all'),
    path('unread/count/', views.unread_count_json, name='unread_count'),
]
