from django.urls import path
from . import views

urlpatterns = [
    path('checkout/<int:reservation_id>/', views.payment_checkout_view, name='payment_checkout'),
    path('status/<int:payment_id>/', views.payment_status_view, name='payment_status'),
    path('history/', views.payment_history_view, name='payment_history'),
    path('staff/', views.staff_payments_view, name='staff_payments'),
    path('staff/verify/<int:payment_id>/', views.verify_payment_view, name='verify_payment'),
    path('proof/<int:payment_id>/', views.view_payment_proof_view, name='view_payment_proof'),
    path('reports/', views.revenue_report_view, name='revenue_report'),
]
