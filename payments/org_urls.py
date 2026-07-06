from django.urls import path
from . import views

urlpatterns = [
    # Org Admin - Payment Management
    path('payments/', views.staff_payments_view, name='org_admin_payments'),
    path('payments/verify/<int:payment_id>/', views.verify_payment_view, name='org_admin_verify_payment'),
    path('payments/cash-confirm/<int:payment_id>/', views.cash_payment_confirmation_view, name='org_admin_cash_payment_confirm'),
]
