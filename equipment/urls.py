from django.urls import path
from . import views

urlpatterns = [
    path('', views.equipment_list_view, name='equipment_list'),
    path('rent/', views.equipment_rental_create_view, name='equipment_rental_create'),
    path('staff/', views.staff_equipment_view, name='staff_equipment'),
    path('staff/checkout/<int:rental_id>/', views.check_out_equipment_view, name='check_out_equipment'),
    path('staff/checkin/<int:rental_id>/', views.check_in_equipment_view, name='check_in_equipment'),
    path('manage/', views.admin_equipment_list_view, name='admin_equipment_list'),
    path('manage/create/', views.admin_equipment_create_view, name='admin_equipment_create'),
    path('manage/<int:equipment_id>/edit/', views.admin_equipment_edit_view, name='admin_equipment_edit'),
    path('manage/<int:equipment_id>/delete/', views.admin_equipment_delete_view, name='admin_equipment_delete'),
    path('<int:equipment_id>/', views.equipment_detail_view, name='equipment_detail'),
]
