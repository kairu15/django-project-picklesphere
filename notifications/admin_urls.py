from django.urls import path
from . import views

urlpatterns = [
    path('smtp-settings/', views.smtp_settings_view, name='super_admin_smtp_settings'),
    path('smtp-settings/test/', views.smtp_test_email_view, name='super_admin_smtp_test'),
    path('email-logs/', views.email_log_list_view, name='super_admin_email_logs'),
    path('email-logs/<int:log_id>/', views.email_log_detail_view, name='super_admin_email_log_detail'),
]
