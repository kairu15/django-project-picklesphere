import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from django.http import HttpResponse, Http404
from datetime import datetime, timedelta
from accounts.decorators import admin_required, staff_or_admin_required, user_required
from .models import Payment, Refund, PaymentLog
from .forms import PaymentMethodForm, GCashPaymentForm, CashPaymentForm, PaymentApprovalForm, RefundRequestForm
from reservations.models import Reservation, CancellationRequest
from notifications.models import Notification


@login_required
def payment_checkout_view(request, reservation_id):
    # Staff/admin can view any reservation, regular users only their own
    if request.user.is_staff_user() or request.user.is_admin():
        reservation = get_object_or_404(Reservation, id=reservation_id)
    else:
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
            form = CashPaymentForm(request.POST, request.FILES, instance=payment)
            if form.is_valid():
                payment = form.save()
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
    
    return render(request, 'user/payments/checkout.html', {
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
    
    return render(request, 'user/payments/payment_status.html', {'payment': payment})


@login_required
@staff_or_admin_required
def staff_payments_view(request):
    
    payments = Payment.objects.all().order_by('-created_at')
    
    # Org-scoping for org_admin and org_staff users
    if request.user.organization:
        payments = payments.filter(reservation__court__organization=request.user.organization)
    
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
    
    # Sorting
    sort_by = request.GET.get('sort_by', '-created_at')
    sort_order = request.GET.get('sort_order', 'desc')
    allowed_sort_fields = ['id', 'amount', 'method', 'status', 'created_at']
    if sort_by.lstrip('-') in allowed_sort_fields:
        if sort_order == 'asc' and sort_by.startswith('-'):
            sort_by = sort_by[1:]
        elif sort_order == 'desc' and not sort_by.startswith('-'):
            sort_by = '-' + sort_by
        payments = payments.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(payments, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Statistics (scoped for org)
    base_paid = Payment.objects.filter(status='paid')
    base_pending = Payment.objects.filter(status='pending')
    if request.user.organization:
        org_filter = Q(reservation__court__organization=request.user.organization)
        base_paid = base_paid.filter(org_filter)
        base_pending = base_pending.filter(org_filter)
    
    total_paid = base_paid.aggregate(Sum('amount'))['amount__sum'] or 0
    total_pending = base_pending.aggregate(Sum('amount'))['amount__sum'] or 0
    
    today_paid = base_paid.filter(
        created_at__date=timezone.now().date()
    )
    today_revenue = today_paid.aggregate(Sum('amount'))['amount__sum'] or 0
    
    return render(request, 'staff/payments/staff_payments.html', {
        'payments': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'status_filter': status_filter,
        'method_filter': method_filter,
        'date_from': date_from,
        'date_to': date_to,
        'sort_by': sort_by,
        'sort_order': sort_order,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'today_revenue': today_revenue
    })


@login_required
@staff_or_admin_required
def verify_payment_view(request, payment_id):

    payment = get_object_or_404(Payment, id=payment_id)

    # Determine template and redirect URL based on user role and URL path
    is_admin_url = 'admin' in request.path
    if request.user.is_admin() and is_admin_url:
        template_name = 'admin/payments/verify_payment.html'
        redirect_url = 'admin_payments'
    else:
        template_name = 'staff/payments/verify_payment.html'
        redirect_url = 'staff_payments'

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
            return redirect(redirect_url)
    else:
        form = PaymentApprovalForm(instance=payment)

    return render(request, template_name, {
        'form': form,
        'payment': payment
    })


@login_required
@user_required
def payment_history_view(request):
    payments = Payment.objects.filter(reservation__user=request.user).order_by('-created_at')
    
    # Compute stats
    total_spent = payments.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    paid_count = payments.filter(status='paid').count()
    pending_count = payments.filter(status='pending').count()
    refunded_count = payments.filter(status='refunded').count()
    total_count = payments.count()
    
    return render(request, 'user/payments/payment_history.html', {
        'payments': payments,
        'total_spent': total_spent,
        'paid_count': paid_count,
        'pending_count': pending_count,
        'refunded_count': refunded_count,
        'total_count': total_count,
    })


@login_required
def view_payment_proof_view(request, payment_id):
    """View the GCash payment proof image"""
    payment = get_object_or_404(Payment, id=payment_id)

    # Check permissions - user can view their own, staff/admin can view all
    if payment.reservation.user != request.user and not request.user.is_staff_user() and not request.user.is_admin():
        messages.error(request, 'You do not have permission to view this payment proof.')
        return redirect('payment_status', payment_id=payment.id)

    # Check if image exists
    if not payment.gcash_proof_image:
        messages.error(request, 'No payment proof image available for this payment.')
        return redirect('payment_status', payment_id=payment.id)

    return render(request, 'admin/payments/view_proof.html', {
        'payment': payment,
        'proof_image': payment.gcash_proof_image
    })


@login_required
def serve_payment_proof_image(request, payment_id):
    """Serve the payment proof image directly"""
    payment = get_object_or_404(Payment, id=payment_id)

    # Check permissions - user can view their own, staff/admin can view all
    if payment.reservation.user != request.user and not request.user.is_staff_user() and not request.user.is_admin():
        raise Http404("Payment proof not found")

    # Check if image exists
    if not payment.gcash_proof_image or not payment.gcash_proof_image.name:
        raise Http404("Payment proof image not found")

    try:
        # Serve the image file
        with open(payment.gcash_proof_image.path, 'rb') as f:
            image_data = f.read()

        # Determine content type based on file extension
        import os
        content_type = 'image/jpeg'
        if payment.gcash_proof_image.name.lower().endswith('.png'):
            content_type = 'image/png'
        elif payment.gcash_proof_image.name.lower().endswith('.gif'):
            content_type = 'image/gif'
        elif payment.gcash_proof_image.name.lower().endswith('.webp'):
            content_type = 'image/webp'

        response = HttpResponse(image_data, content_type=content_type)
        return response
    except FileNotFoundError:
        raise Http404("Payment proof image file not found")
    except Exception as e:
        raise Http404("Error loading payment proof image")


@login_required
@admin_required
def admin_payments_view(request):
    """Admin-only payment management with enhanced features"""

    payments = Payment.objects.all().order_by('-created_at')
    
    # Org-scoping for org_admin users
    if request.user.is_org_admin() and request.user.organization:
        payments = payments.filter(reservation__court__organization=request.user.organization)

    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        payments = payments.filter(status=status_filter)

    # Filter by method
    method_filter = request.GET.get('method', '')
    if method_filter:
        payments = payments.filter(method=method_filter)

    # Filter by date range
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        payments = payments.filter(created_at__date__gte=date_from)
    if date_to:
        payments = payments.filter(created_at__date__lte=date_to)

    # Filter by user role (who made the payment verification)
    verified_by_filter = request.GET.get('verified_by', '')
    if verified_by_filter:
        if verified_by_filter == 'admin':
            payments = payments.filter(cash_received_by__role='admin')
        elif verified_by_filter == 'staff':
            payments = payments.filter(cash_received_by__role='staff')
        elif verified_by_filter == 'system':
            payments = payments.filter(cash_received_by__isnull=True, method='card')

    # Enhanced Statistics
    today = timezone.now().date()

    # Today's stats
    today_payments = Payment.objects.filter(created_at__date=today)
    today_revenue = today_payments.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    today_count = today_payments.filter(status='paid').count()

    # This week's stats
    week_start = today - timedelta(days=today.weekday())
    week_payments = Payment.objects.filter(created_at__date__gte=week_start)
    week_revenue = week_payments.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    week_count = week_payments.filter(status='paid').count()

    # This month's stats
    month_start = today.replace(day=1)
    month_payments = Payment.objects.filter(created_at__date__gte=month_start)
    month_revenue = month_payments.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    month_count = month_payments.filter(status='paid').count()

    # Overall totals
    total_paid = Payment.objects.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    total_pending = Payment.objects.filter(status='pending').aggregate(Sum('amount'))['amount__sum'] or 0
    total_refunded = Payment.objects.filter(status='refunded').aggregate(Sum('amount'))['amount__sum'] or 0

    # Payment method breakdown
    method_breakdown = Payment.objects.filter(status='paid').values('method').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')

    # Verification stats - who processed payments
    verification_stats = Payment.objects.filter(
        status='paid',
        cash_received_by__isnull=False
    ).values('cash_received_by__role').annotate(
        total=Sum('amount'),
        count=Count('id')
    )

    # Pending verifications (GCash pending)
    pending_gcash = Payment.objects.filter(status='pending', method='gcash').count()
    pending_cash = Payment.objects.filter(status='pending', method='cash').count()

    # Sorting
    sort_by = request.GET.get('sort_by', '-created_at')
    sort_order = request.GET.get('sort_order', 'desc')
    allowed_sort_fields = ['id', 'amount', 'method', 'status', 'created_at']
    if sort_by.lstrip('-') in allowed_sort_fields:
        if sort_order == 'asc' and sort_by.startswith('-'):
            sort_by = sort_by[1:]
        elif sort_order == 'desc' and not sort_by.startswith('-'):
            sort_by = '-' + sort_by
        payments = payments.order_by(sort_by)

    # Pagination
    paginator = Paginator(payments, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Recent payment logs
    recent_logs = PaymentLog.objects.select_related('payment', 'performed_by').order_by('-created_at')[:10]

    context = {
        'payments': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'sort_by': sort_by,
        'sort_order': sort_order,
        'status_filter': status_filter,
        'method_filter': method_filter,
        'date_from': date_from,
        'date_to': date_to,
        'verified_by_filter': verified_by_filter,
        # Stats
        'today_revenue': today_revenue,
        'today_count': today_count,
        'week_revenue': week_revenue,
        'week_count': week_count,
        'month_revenue': month_revenue,
        'month_count': month_count,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'total_refunded': total_refunded,
        # Breakdowns
        'method_breakdown': method_breakdown,
        'verification_stats': verification_stats,
        'pending_gcash': pending_gcash,
        'pending_cash': pending_cash,
        'recent_logs': recent_logs,
    }

    return render(request, 'admin/payments/admin_payments.html', context)


@login_required
@admin_required
def admin_cancellation_refunds_view(request):
    """Admin page for reviewing cancellation refund details and marking payments refunded."""

    cancellations = CancellationRequest.objects.select_related(
        'reservation',
        'reservation__user',
        'reservation__court',
        'requested_by',
    ).order_by('-requested_at')

    if request.method == 'POST':
        cancellation_id = request.POST.get('cancellation_id')
        cancellation = get_object_or_404(cancellations, id=cancellation_id)

        try:
            payment = cancellation.reservation.payment
        except Payment.DoesNotExist:
            messages.error(request, 'No payment record was found for this cancellation.')
            return redirect('admin_cancellation_refunds')

        old_status = payment.status
        original_amount = payment.amount
        refund_amount = original_amount - cancellation.deduction_amount

        now = timezone.now()

        payment.status = 'refunded'
        payment.save(update_fields=['status', 'updated_at'])

        cancellation.refund_processed = True
        cancellation.refund_processed_at = now
        cancellation.save(update_fields=['refund_processed', 'refund_processed_at'])

        refund = Refund.objects.filter(payment=payment).order_by('-requested_at').first()
        created = refund is None
        if created:
            refund = Refund(payment=payment, requested_by=cancellation.requested_by)

        refund.amount = refund_amount
        refund.reason = f"{cancellation.reason} ({cancellation.deduction_percentage}% cancellation fee applied)"
        refund.status = 'processed'
        refund.approved_by = request.user
        refund.approved_at = now
        refund.processed_at = now
        refund.save()

        PaymentLog.objects.create(
            payment=payment,
            action='Payment Refunded',
            details=f'Payment status changed from {old_status} to refunded via Cancellation & Refund page. Refund record #{refund.id} {"created" if created else "updated"}.',
            performed_by=request.user
        )

        Notification.objects.create(
            user=payment.reservation.user,
            message=f"Your payment for reservation #{payment.reservation.id} has been marked as refunded."
        )

        messages.success(request, f'Payment #{payment.id} has been updated to Refunded.')
        return redirect('admin_cancellation_refunds')

    refund_rows = []
    for cancellation in cancellations:
        payment = getattr(cancellation.reservation, 'payment', None)
        original_amount = payment.amount if payment else cancellation.reservation.total_amount
        refund_amount = original_amount - cancellation.deduction_amount
        refund_rows.append({
            'cancellation': cancellation,
            'payment': payment,
            'original_amount': original_amount,
            'refund_amount': refund_amount,
        })

    return render(request, 'admin/payments/cancellation_refunds.html', {
        'refund_rows': refund_rows,
    })


@login_required
@admin_required
def revenue_report_view(request):

    # Date range
    date_from = request.GET.get('date_from', (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.GET.get('date_to', timezone.now().strftime('%Y-%m-%d'))
    court_filter = request.GET.get('court', '')
    method_filter = request.GET.get('method', '')

    # Base payments queryset
    payments = Payment.objects.filter(
        status='paid',
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    ).select_related('reservation', 'reservation__court', 'reservation__user')
    
    # Org-scoping for org_admin users
    if request.user.is_org_admin() and request.user.organization:
        payments = payments.filter(reservation__court__organization=request.user.organization)

    if court_filter:
        payments = payments.filter(reservation__court_id=court_filter)
    if method_filter:
        payments = payments.filter(method=method_filter)

    today = timezone.now().date()
    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
    days_in_range = (date_to_obj - date_from_obj).days + 1

    # ==================== 1. SUMMARY METRICS ====================

    # Total revenue for selected period
    total_revenue = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    total_paid_bookings = payments.count()
    avg_revenue_per_booking = total_revenue / total_paid_bookings if total_paid_bookings > 0 else 0

    # Daily revenue
    daily_revenue = payments.count()
    avg_revenue_per_day = total_revenue / days_in_range if days_in_range > 0 else 0

    # Org-scoped base paid queryset for all downstream stats
    base_paid_qs = Payment.objects.filter(status='paid')
    if request.user.is_org_admin() and request.user.organization:
        base_paid_qs = base_paid_qs.filter(reservation__court__organization=request.user.organization)

    # Weekly revenue (current week)
    week_start = today - timedelta(days=today.weekday())
    weekly_revenue = base_paid_qs.filter(
        created_at__date__gte=week_start,
        created_at__date__lte=today
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # Monthly revenue (current month)
    month_start = today.replace(day=1)
    monthly_revenue = base_paid_qs.filter(
        created_at__date__gte=month_start,
        created_at__date__lte=today
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # Yearly revenue (current year)
    year_start = today.replace(month=1, day=1)
    yearly_revenue = base_paid_qs.filter(
        created_at__date__gte=year_start,
        created_at__date__lte=today
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # Revenue growth comparison (previous period)
    prev_date_from = date_from_obj - timedelta(days=days_in_range)
    prev_date_to = date_from_obj - timedelta(days=1)
    prev_payments = base_paid_qs.filter(
        created_at__date__gte=prev_date_from,
        created_at__date__lte=prev_date_to
    )
    prev_revenue = prev_payments.aggregate(Sum('amount'))['amount__sum'] or 0
    revenue_growth = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0

    # Booking growth
    prev_bookings = prev_payments.count()
    booking_growth = ((total_paid_bookings - prev_bookings) / prev_bookings * 100) if prev_bookings > 0 else 0

    summary_metrics = {
        'total_revenue': total_revenue,
        'daily_revenue': daily_revenue,
        'weekly_revenue': weekly_revenue,
        'monthly_revenue': monthly_revenue,
        'yearly_revenue': yearly_revenue,
        'total_paid_bookings': total_paid_bookings,
        'avg_revenue_per_booking': avg_revenue_per_booking,
        'avg_revenue_per_day': avg_revenue_per_day,
        'revenue_growth': revenue_growth,
        'booking_growth': booking_growth,
        'prev_revenue': prev_revenue,
        'prev_bookings': prev_bookings,
    }

    # ==================== 2. REVENUE BY SOURCE ====================

    # Court reservations (hourly rentals)
    court_reservations = payments.filter(
        reservation__match_name__isnull=True
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Game/match fees (organized play, tournaments)
    game_fees = payments.filter(
        reservation__match_name__isnull=False
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Equipment rentals
    equipment_revenue = payments.filter(
        reservation__equipment_fee__gt=0
    ).aggregate(
        total=Sum('reservation__equipment_fee')
    )['total'] or 0

    # Court fees only (subtotal)
    court_fees_only = payments.aggregate(
        total=Sum('reservation__subtotal')
    )['total'] or 0

    revenue_by_source = {
        'court_reservations': court_reservations,
        'game_fees': game_fees,
        'equipment_rentals': equipment_revenue,
        'court_fees_only': court_fees_only,
    }

    # ==================== 3. BOOKING DETAILS ====================

    booking_details = payments.select_related('reservation', 'reservation__court').prefetch_related(
        'reservation__rented_equipment', 'reservation__rented_equipment__equipment'
    ).order_by('-created_at')

    # ==================== 4. PAYMENT INFORMATION ====================

    # Revenue by payment method
    revenue_by_method_list = list(payments.values('method').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total'))

    # Calculate percentages
    total_rev = summary_metrics['total_revenue']
    for item in revenue_by_method_list:
        item['percentage'] = (float(item['total'] or 0) / float(total_rev) * 100) if total_rev > 0 else 0

    # Org-scoped base all-status queryset for breakdown stats
    base_all_qs = Payment.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    )
    if request.user.is_org_admin() and request.user.organization:
        base_all_qs = base_all_qs.filter(reservation__court__organization=request.user.organization)

    # Payment status breakdown
    payment_status_breakdown = base_all_qs.values('status').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')

    # Pending payments
    pending_payments = base_all_qs.filter(
        status='pending'
    ).aggregate(total=Sum('amount'))['total'] or 0

    payment_info = {
        'revenue_by_method': revenue_by_method_list,
        'status_breakdown': payment_status_breakdown,
        'pending_amount': pending_payments,
    }

    # ==================== 5. DISCOUNTS AND PROMOTIONS ====================

    # Calculate potential discounts (difference between standard rate and actual)
    from django.db.models import ExpressionWrapper, FloatField
    standard_rate_revenue = payments.aggregate(
        total=Sum(ExpressionWrapper(
            F('reservation__court__hourly_rate') * F('reservation__duration_hours'),
            output_field=FloatField()
        ))
    )['total'] or 0

    # Off-peak analysis (early morning and late evening bookings)
    off_peak_bookings = payments.filter(
        Q(reservation__start_time__hour__lt=8) | Q(reservation__start_time__hour__gte=18)
    ).count()

    discounts_data = {
        'off_peak_bookings': off_peak_bookings,
    }

    # ==================== 6. REFUNDS AND CANCELLATIONS ====================

    # Refunds processed
    refunds = Refund.objects.filter(
        status='processed',
        processed_at__date__gte=date_from,
        processed_at__date__lte=date_to
    )
    if request.user.is_org_admin() and request.user.organization:
        refunds = refunds.filter(payment__reservation__court__organization=request.user.organization)
    total_refunds = refunds.aggregate(total=Sum('amount'))['total'] or 0
    refund_count = refunds.count()

    # Cancelled reservations (no-show or cancelled)
    cancelled_base_qs = Payment.objects.filter(
        reservation__status__in=['cancelled', 'rejected'],
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    )
    if request.user.is_org_admin() and request.user.organization:
        cancelled_base_qs = cancelled_base_qs.filter(reservation__court__organization=request.user.organization)
    cancelled_revenue = cancelled_base_qs.aggregate(total=Sum('amount'))['total'] or 0
    cancelled_count = cancelled_base_qs.count()

    refunds_data = {
        'total_refunds': total_refunds,
        'refund_count': refund_count,
        'cancelled_revenue': cancelled_revenue,
        'cancelled_count': cancelled_count,
        'net_revenue': total_revenue - total_refunds,
    }

    # ==================== 7. CHARTS DATA ====================

    # Daily revenue for chart
    daily_revenue_chart = payments.extra(
        select={'date': 'DATE(payments.created_at)'}
    ).values('date').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('date')

    # Revenue by court
    revenue_by_court = payments.values('reservation__court__name').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')

    # Hourly distribution - use values from related reservation
    from django.db.models.functions import ExtractHour
    hourly_distribution = payments.annotate(
        hour=ExtractHour('reservation__start_time')
    ).values('hour').annotate(
        count=Count('id'),
        revenue=Sum('amount')
    ).order_by('hour')

    # Prepare chart data for JSON serialization
    chart_data = {
        'daily_labels': [item['date'].strftime('%b %d') if hasattr(item['date'], 'strftime') else str(item['date'])[:6] for item in daily_revenue_chart],
        'daily_revenue': [float(item['total'] or 0) for item in daily_revenue_chart],
        'daily_bookings': [item['count'] for item in daily_revenue_chart],
        'court_labels': [item['reservation__court__name'] or 'Unknown' for item in revenue_by_court],
        'court_revenue': [float(item['total'] or 0) for item in revenue_by_court],
        'hourly_labels': [f"{int(item['hour'] or 0)}:00" for item in hourly_distribution],
        'hourly_bookings': [item['count'] for item in hourly_distribution],
        'hourly_revenue': [float(item['revenue'] or 0) for item in hourly_distribution],
    }

    # Court list for filter
    from courts.models import Court
    courts = Court.objects.filter(is_active=True)

    return render(request, 'admin/payments/revenue_report.html', {
        'date_from': date_from,
        'date_to': date_to,
        'court_filter': court_filter,
        'method_filter': method_filter,
        'summary_metrics': summary_metrics,
        'revenue_by_source': revenue_by_source,
        'booking_details': booking_details,
        'payment_info': payment_info,
        'discounts_data': discounts_data,
        'refunds_data': refunds_data,
        'daily_revenue_chart': daily_revenue_chart,
        'revenue_by_court': revenue_by_court,
        'hourly_distribution': hourly_distribution,
        'chart_data': chart_data,
        'courts': courts,
    })


@login_required
@admin_required
def revenue_report_export_view(request):
    """Export revenue report as CSV"""
    import csv
    from django.http import HttpResponse

    # Get filters
    date_from = request.GET.get('date_from', (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.GET.get('date_to', timezone.now().strftime('%Y-%m-%d'))
    court_filter = request.GET.get('court', '')
    method_filter = request.GET.get('method', '')
    export_format = request.GET.get('format', 'csv')

    # Base payments queryset
    payments = Payment.objects.filter(
        status='paid',
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    ).select_related('reservation', 'reservation__court', 'reservation__user')
    
    # Org-scoping for org_admin users
    if request.user.is_org_admin() and request.user.organization:
        payments = payments.filter(reservation__court__organization=request.user.organization)

    if court_filter:
        payments = payments.filter(reservation__court_id=court_filter)
    if method_filter:
        payments = payments.filter(method=method_filter)

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="revenue_report_{date_from}_to_{date_to}.csv"'

    writer = csv.writer(response)

    # Write header
    writer.writerow([
        'Revenue Report',
        f'From: {date_from}',
        f'To: {date_to}',
        ''
    ])
    writer.writerow([])

    # Summary Section
    total_revenue = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    total_bookings = payments.count()
    writer.writerow(['SUMMARY METRICS'])
    writer.writerow(['Total Revenue', f'₱{total_revenue:.2f}'])
    writer.writerow(['Total Bookings', total_bookings])
    writer.writerow([])

    # Booking Details
    writer.writerow(['BOOKING DETAILS'])
    writer.writerow([
        'Booking ID', 'Date', 'Start Time', 'End Time', 'Court',
        'Player Name', 'Duration (hrs)', 'Equipment Fee',
        'Court Fee', 'Total Amount', 'Payment Method', 'Transaction ID', 'Status'
    ])

    for payment in payments:
        reservation = payment.reservation
        writer.writerow([
            reservation.id,
            reservation.date,
            reservation.start_time,
            reservation.end_time,
            reservation.court.name if reservation.court else 'N/A',
            reservation.user.get_full_name() or reservation.user.username,
            reservation.duration_hours,
            reservation.equipment_fee,
            reservation.subtotal,
            payment.amount,
            payment.method or 'N/A',
            payment.transaction_id or 'N/A',
            payment.status
        ])

    writer.writerow([])

    # Revenue by Method
    revenue_by_method = payments.values('method').annotate(
        total=Sum('amount'),
        count=Count('id')
    )
    writer.writerow(['REVENUE BY PAYMENT METHOD'])
    writer.writerow(['Method', 'Transactions', 'Revenue'])
    for item in revenue_by_method:
        writer.writerow([
            item['method'] or 'N/A',
            item['count'],
            f"₱{item['total']:.2f}"
        ])

    return response
