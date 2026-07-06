from django.urls import path
from . import views

urlpatterns = [
    # Org Admin - Dashboard & Settings
    path('dashboard/', views.org_admin_dashboard, name='org_admin_dashboard'),
    path('profile/', views.org_admin_profile, name='org_admin_profile'),
    path('staff/', views.org_admin_manage_staff, name='org_admin_manage_staff'),
    path('location/', views.org_admin_location_setup, name='org_admin_location_setup'),
    path('api/reverse-geocode/', views.reverse_geocode_api, name='org_admin_reverse_geocode'),
]
