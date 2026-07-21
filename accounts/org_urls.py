from django.urls import path
from . import views

urlpatterns = [
    # Org Admin - User Management
    # Note: staff/ is defined in organizations.org_urls (org_admin_manage_staff)
    path('staff/create/', views.user_create_view, name='org_admin_staff_create'),
    path('staff/edit/<int:user_id>/', views.user_edit_view, name='org_admin_staff_edit'),
    path('staff/<int:user_id>/delete/', views.user_delete_view, name='org_admin_staff_delete'),
]
