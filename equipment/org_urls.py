from django.urls import path
from . import views

urlpatterns = [
    # Org Admin - Equipment Management
    path('equipment/', views.org_admin_equipment_list_view, name='org_admin_equipment_list'),
    path('equipment/create/', views.org_admin_equipment_create_view, name='org_admin_equipment_create'),
    path('equipment/<int:equipment_id>/', views.org_admin_equipment_detail_view, name='org_admin_equipment_detail'),
    path('equipment/<int:equipment_id>/edit/', views.org_admin_equipment_edit_view, name='org_admin_equipment_edit'),
    path('equipment/<int:equipment_id>/delete/', views.org_admin_equipment_delete_view, name='org_admin_equipment_delete'),
]
