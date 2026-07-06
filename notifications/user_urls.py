from django.urls import path
from . import views

urlpatterns = [
    # User - Notifications
    path('notifications/', views.notification_list_view, name='notification_list'),
    path('notifications/<int:notification_id>/', views.notification_detail_view, name='notification_detail'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read_view, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_read_view, name='mark_all_read'),
    path('notifications/<int:notification_id>/delete/', views.delete_notification_view, name='delete_notification'),
]
