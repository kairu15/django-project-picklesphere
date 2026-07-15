from django.urls import path
from . import views
from accounts import views as accounts_views

urlpatterns = [
    # Org Admin - Dashboard & Settings
    path('dashboard/', views.org_admin_dashboard, name='org_admin_dashboard'),
    path('profile/', views.org_admin_profile, name='org_admin_profile'),
    path('my-profile/', accounts_views.profile_view, name='org_admin_personal_profile'),
    path('staff/', views.org_admin_manage_staff, name='org_admin_manage_staff'),
    path('location/', views.org_admin_location_setup, name='org_admin_location_setup'),
    path('activity-log/', views.org_admin_org_activity_log, name='org_admin_org_activity_log'),
    path('analytics/', views.org_admin_analytics_view, name='org_admin_analytics'),
    path('api/reverse-geocode/', views.reverse_geocode_api, name='org_admin_reverse_geocode'),
]
