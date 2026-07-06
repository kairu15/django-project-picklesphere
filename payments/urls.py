from django.urls import path
from . import views

urlpatterns = [
    path('checkout/<int:reservation_id>/', views.payment_checkout_view, name='payment_checkout'),
    path('status/<int:payment_id>/', views.payment_status_view, name='payment_status'),
    path('history/', views.payment_history_view, name='payment_history'),
    path('staff/', views.staff_payments_view, name='staff_payments'),
    path('staff/verify/<int:payment_id>/', views.verify_payment_view, name='verify_payment'),
    path('staff/cash-confirm/<int:payment_id>/', views.cash_payment_confirmation_view, name='cash_payment_confirm'),
    path('admin/', views.admin_payments_view, name='admin_payments'),
    path('admin/cancellation-refunds/', views.admin_cancellation_refunds_view, name='admin_cancellation_refunds'),
    path('admin/verify/<int:payment_id>/', views.verify_payment_view, name='admin_verify_payment'),
    path('proof/<int:payment_id>/', views.view_payment_proof_view, name='view_payment_proof'),
    path('proof-image/<int:payment_id>/', views.serve_payment_proof_image, name='serve_payment_proof_image'),
    path('reports/', views.revenue_report_view, name='revenue_report'),
    path('reports/export/', views.revenue_report_export_view, name='revenue_report_export'),
]
