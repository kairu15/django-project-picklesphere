import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Payment, Refund, PaymentLog
from .forms import PaymentMethodForm, GCashPaymentForm, CashPaymentForm, PaymentApprovalForm, RefundRequestForm
from reservations.models import Reservation
from notifications.models import Notification


@login_required
def payment_checkout_view(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    
    # Check if payment already exists
    try:
        payment = Payment.objects.get(reservation=reservation)
    except Payment.DoesNotExist:
        payment = None
    
    if request.method == 'POST':
        method = request.POST.get('method')
        
        if not payment:
            payment = Payment.objects.create(
                reservation=reservation,
                amount=reservation.total_amount,
                status='pending'
            )
        
        payment.method = method
        
        if method == 'gcash':
            form = GCashPaymentForm(request.POST, request.FILES, instance=payment)
            if form.is_valid():
                payment = form.save()
                payment.status = 'pending'
                payment.save()
                
                # Log the payment
                PaymentLog.objects.create(
                    payment=payment,
                    action='GCash Payment Submitted',
                    details=f'GCash reference: {payment.gcash_reference}',
                    performed_by=request.user
                )
                
                # Notify staff
                from accounts.models import User
                staff_users = User.objects.filter(role__in=['staff', 'admin'])
                for staff in staff_users:
                    Notification.objects.create(
                        user=staff,
                        message=f"New GCash payment for reservation #{reservation.id} requires verification."
                    )
                
                messages.success(request, 'GCash payment details submitted. Please wait for verification.')
                return redirect('payment_status', payment_id=payment.id)
                
        elif method == 'cash':
            payment.status = 'pending'
            payment.save()
            
            PaymentLog.objects.create(
                payment=payment,
                action='Cash Payment Selected',
                details='User selected cash payment method',
                performed_by=request.user
            )
            
            messages.success(request, 'Please proceed to the counter to complete your cash payment.')
            return redirect('payment_status', payment_id=payment.id)
            
        elif method == 'card':
            # Generate transaction ID for card payment
            payment.transaction_id = str(uuid.uuid4())[:8].upper()
            payment.status = 'paid'
            payment.save()
            
            PaymentLog.objects.create(
                payment=payment,
                action='Card Payment Processed',
                details=f'Transaction ID: {payment.transaction_id}',
                performed_by=request.user
            )
            
            # Confirm the reservation
            reservation.status = 'confirmed'
            reservation.save()
            
            Notification.objects.create(
                user=request.user,
                message=f"Payment successful for reservation #{reservation.id}. Your reservation is confirmed!"
            )
            
            messages.success(request, 'Payment successful! Your reservation is confirmed.')
            return redirect('reservation_detail', reservation_id=reservation.id)
    else:
        gcash_form = GCashPaymentForm(instance=payment) if payment else GCashPaymentForm()
        cash_form = CashPaymentForm(instance=payment) if payment else CashPaymentForm()
    
    return render(request, 'payments/checkout.html', {
        'reservation': reservation,
        'payment': payment,
        'gcash_form': gcash_form,
        'cash_form': cash_form
    })


@login_required
def payment_status_view(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    
    # Check permissions
    if payment.reservation.user != request.user and not request.user.is_staff_user() and not request.user.is_admin():
        messages.error(request, 'You do not have permission to view this payment.')
        return redirect('dashboard')
    
    return render(request, 'payments/payment_status.html', {'payment': payment})


@login_required
def staff_payments_view(request):
    if not request.user.is_staff_user() and not request.user.is_admin():
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')
    
    payments = Payment.objects.all().order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        payments = payments.filter(status=status_filter)
    
    # Filter by method
    method_filter = request.GET.get('method', '')
    if method_filter:
        payments = payments.filter(method=method_filter)
    
    # Filter by date
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        payments = payments.filter(created_at__date__gte=date_from)
    if date_to:
        payments = payments.filter(created_at__date__lte=date_to)
    
    # Statistics
    total_paid = Payment.objects.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    total_pending = Payment.objects.filter(status='pending').aggregate(Sum('amount'))['amount__sum'] or 0
    today_revenue = Payment.objects.filter(
        status='paid',
        created_at__date=timezone.now().date()
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    return render(request, 'payments/staff_payments.html', {
        'payments': payments,
        'status_filter': status_filter,
        'method_filter': method_filter,
        'date_from': date_from,
        'date_to': date_to,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'today_revenue': today_revenue
    })


@login_required
def verify_payment_view(request, payment_id):
    if not request.user.is_staff_user() and not request.user.is_admin():
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('dashboard')
    
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.method == 'POST':
        form = PaymentApprovalForm(request.POST, instance=payment)
        if form.is_valid():
            old_status = payment.status
            payment = form.save()
            
            # Update reservation status if payment is verified
            if payment.status == 'paid' and old_status != 'paid':
                payment.reservation.status = 'confirmed'
                payment.reservation.save()
                
                # Set cash payment details
                if payment.method == 'cash':
                    payment.cash_received_by = request.user
                    payment.cash_received_at = timezone.now()
                    payment.save()
                
                # Notify user
                Notification.objects.create(
                    user=payment.reservation.user,
                    message=f"Your payment for reservation #{payment.reservation.id} has been verified. Your reservation is confirmed!"
                )
            
            # Log the action
            PaymentLog.objects.create(
                payment=payment,
                action=f'Payment {payment.status}',
                details=f'Payment status changed from {old_status} to {payment.status}',
                performed_by=request.user
            )
            
            messages.success(request, f'Payment #{payment.id} has been {payment.status}.')
            return redirect('staff_payments')
    else:
        form = PaymentApprovalForm(instance=payment)
    
    return render(request, 'payments/verify_payment.html', {
        'form': form,
        'payment': payment
    })


@login_required
def payment_history_view(request):
    payments = Payment.objects.filter(reservation__user=request.user).order_by('-created_at')
    
    return render(request, 'payments/payment_history.html', {
        'payments': payments
    })


@login_required
def revenue_report_view(request):
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')
    
    # Date range
    date_from = request.GET.get('date_from', (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.GET.get('date_to', timezone.now().strftime('%Y-%m-%d'))
    
    payments = Payment.objects.filter(
        status='paid',
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    )
    
    # Revenue by method
    revenue_by_method = payments.values('method').annotate(
        total=Sum('amount'),
        count=Count('id')
    )
    
    # Daily revenue
    daily_revenue = payments.extra(
        select={'date': 'DATE(created_at)'}
    ).values('date').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('date')
    
    total_revenue = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    total_transactions = payments.count()
    
    return render(request, 'payments/revenue_report.html', {
        'date_from': date_from,
        'date_to': date_to,
        'total_revenue': total_revenue,
        'total_transactions': total_transactions,
        'revenue_by_method': revenue_by_method,
        'daily_revenue': daily_revenue
    })
