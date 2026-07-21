from django.urls import path
from . import views
from accounts import views as accounts_views

urlpatterns = [
    # Org Admin - Dashboard & Settings
    path('dashboard/', views.org_admin_dashboard, name='org_admin_dashboard'),
    path('profile/', views.org_admin_profile, name='org_admin_profile'),
    path('my-profile/', accounts_views.profile_view, name='org_admin_personal_profile'),
    path('staff/', views.org_admin_manage_staff, name='org_admin_manage_staff'),
    path('staff/export/csv/', views.org_admin_staff_export_csv, name='org_admin_staff_export_csv'),
    path('staff/create/', views.org_admin_staff_create, name='org_admin_staff_create'),
    path('staff/<int:staff_id>/', views.org_admin_staff_detail, name='org_admin_staff_detail'),
    path('staff/<int:staff_id>/edit/', views.org_admin_staff_edit, name='org_admin_staff_edit'),
    path('staff/<int:staff_id>/permissions/', views.org_admin_staff_permissions, name='org_admin_staff_permissions'),
    path('staff/<int:staff_id>/toggle-status/', views.org_admin_staff_toggle_status, name='org_admin_staff_toggle_status'),
    path('staff/<int:staff_id>/reset-password/', views.org_admin_staff_reset_password, name='org_admin_staff_reset_password'),
    path('staff/<int:staff_id>/delete/', views.org_admin_staff_delete, name='org_admin_staff_delete'),
    path('location/', views.org_admin_location_setup, name='org_admin_location_setup'),
    path('activity-log/', views.org_admin_org_activity_log, name='org_admin_org_activity_log'),
    path('analytics/', views.org_admin_analytics_view, name='org_admin_analytics'),
    path('api/reverse-geocode/', views.reverse_geocode_api, name='org_admin_reverse_geocode'),
]
