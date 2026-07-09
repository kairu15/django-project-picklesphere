from django.urls import path
from . import views

urlpatterns = [
    # Super Admin - Dashboard
    path('dashboard/', views.super_admin_dashboard, name='super_admin_org_dashboard'),

    # Super Admin - Organization Management
    path('organizations/', views.super_admin_organization_list, name='super_admin_organization_list'),
    path('organizations/<int:pk>/', views.super_admin_organization_detail, name='super_admin_organization_detail'),
    path('organizations/<int:pk>/approve/', views.super_admin_approve_organization, name='super_admin_approve_organization'),
    path('organizations/<int:pk>/toggle-status/', views.super_admin_toggle_org_status, name='super_admin_toggle_org_status'),
    path('organizations/<int:pk>/verify/', views.super_admin_verify_organization, name='super_admin_verify_organization'),
    path('organizations/create/', views.super_admin_organization_create, name='super_admin_organization_create'),
    path('organizations/<int:pk>/edit/', views.super_admin_organization_edit, name='super_admin_organization_edit'),
    path('organizations/<int:pk>/delete/', views.super_admin_organization_delete, name='super_admin_organization_delete'),

    # Super Admin - Organization Activity Logs
    path('organization-activity/', views.super_admin_organization_activity_log, name='super_admin_organization_activity_log'),
]
