from django.urls import path
from . import views

urlpatterns = [
    path('', views.court_list_view, name='court_list'),
    path('manage/', views.admin_court_list_view, name='admin_court_list'),
    path('manage/create/', views.admin_court_create_view, name='admin_court_create'),
    path('manage/<int:court_id>/edit/', views.admin_court_edit_view, name='admin_court_edit'),
    path('manage/<int:court_id>/delete/', views.admin_court_delete_view, name='admin_court_delete'),
    path('sites/', views.admin_site_list_view, name='admin_site_list'),
    path('sites/create/', views.admin_site_create_view, name='admin_site_create'),
    path('sites/<int:site_id>/edit/', views.admin_site_edit_view, name='admin_site_edit'),
    path('sites/<int:site_id>/delete/', views.admin_site_delete_view, name='admin_site_delete'),
    path('<int:court_id>/', views.court_detail_view, name='court_detail'),
    path('<int:court_id>/availability/', views.court_availability_view, name='court_availability'),
]
