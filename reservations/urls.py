from django.urls import path
from . import views

urlpatterns = [
    path('', views.reservation_list_view, name='reservation_list'),
    path('create/', views.reservation_create_view, name='reservation_create'),
    path('api/time-slots/', views.get_time_slots_api, name='get_time_slots'),
    path('api/monthly-availability/', views.get_monthly_availability_api, name='get_monthly_availability'),
    path('api/verify-slot/', views.verify_slot_api, name='verify_slot'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('staff/', views.staff_reservations_view, name='staff_reservations'),
    path('staff/cancellations/', views.staff_cancellations_view, name='staff_cancellations'),
    path('staff/refunds/', views.staff_refund_processing_view, name='staff_refund_processing'),
    path('staff/refunds/history/', views.staff_refund_history_view, name='staff_refund_history'),
    path('staff/<int:reservation_id>/approve/', views.approve_reservation_view, name='approve_reservation'),
    path('manage/', views.admin_reservation_list_view, name='admin_reservation_list'),
    path('manage/create/', views.admin_reservation_create_view, name='admin_reservation_create'),
    path('manage/<int:reservation_id>/edit/', views.admin_reservation_edit_view, name='admin_reservation_edit'),
    path('manage/<int:reservation_id>/delete/', views.admin_reservation_delete_view, name='admin_reservation_delete'),
    path('<int:reservation_id>/', views.reservation_detail_view, name='reservation_detail'),
    path('<int:reservation_id>/edit/', views.reservation_edit_view, name='reservation_edit'),
    path('<int:reservation_id>/cancel/', views.cancel_reservation_view, name='cancel_reservation'),
]
