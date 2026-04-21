from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification_list_view, name='notification_list'),
    path('<int:notification_id>/', views.notification_detail_view, name='notification_detail'),
    path('<int:notification_id>/read/', views.mark_notification_read_view, name='mark_notification_read'),
    path('mark-all-read/', views.mark_all_read_view, name='mark_all_read'),
    path('<int:notification_id>/delete/', views.delete_notification_view, name='delete_notification'),
    path('broadcast/', views.broadcast_message_view, name='broadcast_message'),
    path('broadcast/list/', views.broadcast_list_view, name='broadcast_list'),
]
