from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('all_courts/', views.all_courts_view, name='all_courts'),
    path('court/<int:court_id>/', views.court_view_view, name='court_view'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/user/', views.user_dashboard_view, name='user_dashboard'),
    path('dashboard/staff/', views.staff_dashboard_view, name='staff_dashboard'),
    path('dashboard/admin/', views.admin_dashboard_view, name='admin_dashboard'),
]
