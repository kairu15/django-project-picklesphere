from django.urls import path
from . import views

urlpatterns = [
    # Broadcast (super admin and org admin) - accessible via /notifications/
    # User notification routes are under /user/notifications/ via notifications.user_urls
    path('broadcast/', views.broadcast_message_view, name='broadcast_message'),
    path('broadcast/list/', views.broadcast_list_view, name='broadcast_list'),
]
