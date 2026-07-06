from django.urls import path
from . import views

urlpatterns = [
    # Public URLs
    path('', views.organization_directory, name='organization_directory'),
    path('register/', views.organization_register, name='organization_register'),
    path('<slug:slug>/', views.organization_public_detail, name='organization_public_detail'),
    
    # Super Admin URLs
    path('super-admin/dashboard/', views.super_admin_dashboard, name='super_admin_dashboard'),
    path('super-admin/organizations/', views.super_admin_organization_list, name='super_admin_organization_list'),
    path('super-admin/organizations/<int:pk>/', views.super_admin_organization_detail, name='super_admin_organization_detail'),
    path('super-admin/organizations/<int:pk>/approve/', views.super_admin_approve_organization, name='super_admin_approve_organization'),
    path('super-admin/organizations/<int:pk>/toggle-status/', views.super_admin_toggle_org_status, name='super_admin_toggle_org_status'),
    
    # Org Admin URLs
    path('org-admin/dashboard/', views.org_admin_dashboard, name='org_admin_dashboard'),
    path('org-admin/profile/', views.org_admin_profile, name='org_admin_profile'),
]
