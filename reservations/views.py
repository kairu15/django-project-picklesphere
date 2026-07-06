from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta, date as date_type
from accounts.decorators import admin_required, staff_or_admin_required, user_required
from .models import Reservation, ReservationEquipment, CancellationRequest, CancellationPolicy
from .forms import ReservationForm, ReservationApprovalForm, CancellationRequestForm, AdminReservationForm
from payments.models import Payment
from notifications.models import Notification
from equipment.models import Equipment
from accounts.models import User
from courts.models import Court


@login_required
@user_required
def reservation_list_view(request):
    reservations = Reservation.objects.filter(user=request.user).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        reservations = reservations.filter(status=status_filter)
    
    # Filter by date range
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        reservations = reservations.filter(date__gte=date_from)
    if date_to:
        reservations = reservations.filter(date__lte=date_to)
    
    return render(request, 'user/reservations/reservation_list.html', {
        'reservations': reservations,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to
    })


@login_required
@user_required
def reservation_create_view(request):
    # Fetch active match settings from database
    from scoring.models import MatchSettings
    active_settings = MatchSettings.objects.filter(is_active=True).first()
    
    if request.method == 'POST':
        form = ReservationForm(request.POST, user=request.user)
        equipment_ids = request.POST.getlist('equipment')
        
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.hourly_rate = reservation.court.hourly_rate
            
            # Apply match settings from admin configuration
            if active_settings:
                reservation.match_format = active_settings.format
                reservation.game_type = active_settings.game_type
                reservation.scoring_format = active_settings.scoring_format
                reservation.points_per_game = active_settings.points_per_game
                reservation.games_to_win = active_settings.games_to_win
                reservation.win_by_two = active_settings.win_by_two
            
            reservation.save()
            
            # Add equipment
            equipment_fee = 0
            for eq_id in equipment_ids:
                try:
                    equipment = Equipment.objects.get(id=eq_id, is_active=True)
                    if equipment.quantity_available > 0:
                        RentalEquipment = ReservationEquipment(
                            reservation=reservation,
                            equipment=equipment,
                            quantity=1,
                            rental_fee=equipment.rental_price
                        )
                        RentalEquipment.save()
                        equipment_fee += float(equipment.rental_price)
                        equipment.quantity_available -= 1
                        equipment.save()
                except Equipment.DoesNotExist:
                    pass
            
            # Update equipment fee and total
            reservation.equipment_fee = equipment_fee
            reservation.save()
            
            # Create payment record
            Payment.objects.create(
                reservation=reservation,
                amount=reservation.total_amount,
                status='pending'
            )
            
            # Notify staff (scoped to organization)
            court_org = reservation.court.organization
            if court_org:
                staff_users = User.objects.filter(
                    Q(organization=court_org) | Q(role='super_admin'),
                    role__in=['org_admin', 'org_staff', 'super_admin']
                )
            else:
                staff_users = User.objects.filter(role__in=['staff', 'admin'])
            for staff in staff_users:
                Notification.objects.create(
                    user=staff,
                    message=f"New reservation #{reservation.id} by {request.user.username} requires approval."
                )
            
            # Notify user
            Notification.objects.create(
                user=request.user,
                message=f"Your reservation #{reservation.id} has been created and is pending approval."
            )
            
            messages.success(request, 'Reservation created successfully! Please proceed to payment.')
            return redirect('payment_checkout', reservation_id=reservation.id)
    else:
        # Get court from query parameter to pre-select
        initial_court = request.GET.get('court')
        initial_data = {}
        if initial_court:
            try:
                court = Court.objects.get(id=initial_court, is_active=True)
                initial_data['court'] = court.id
            except Court.DoesNotExist:
                pass
        
        # Add match settings from admin configuration as initial values
        if active_settings:
            initial_data['match_format'] = active_settings.format
            initial_data['game_type'] = active_settings.game_type
            initial_data['scoring_format'] = active_settings.scoring_format
            initial_data['points_per_game'] = active_settings.points_per_game
            initial_data['games_to_win'] = active_settings.games_to_win
            initial_data['win_by_two'] = active_settings.win_by_two
        
        form = ReservationForm(user=request.user, initial=initial_data)
    
    equipment_list = Equipment.objects.filter(quantity_available__gt=0, is_active=True)
    
    return render(request, 'user/reservations/reservation_create.html', {
        'form': form,
        'equipment_list': equipment_list
    })


@login_required
def reservation_detail_view(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    # Check if user has permission to view
    if reservation.user != request.user and not request.user.is_staff_user() and not request.user.is_admin():
        messages.error(request, 'You do not have permission to view this reservation.')
        return redirect('reservation_list')
    
    return render(request, 'user/reservations/reservation_detail.html', {'reservation': reservation})


@login_required
@staff_or_admin_required
def staff_reservations_view(request):
    
    reservations = Reservation.objects.select_related('user', 'court', 'court__site', 'payment').all().order_by('-created_at')
    
    # Org-scoping for org_admin and org_staff users
    if request.user.organization:
        reservations = reservations.filter(court__organization=request.user.organization)
    
    # Search
    search_query = request.GET.get('search', '').strip()
    if search_query:
        reservations = reservations.filter(
            Q(id__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        reservations = reservations.filter(status=status_filter)
    
    # Filter by date
    date_filter = request.GET.get('date', '')
    if date_filter:
        reservations = reservations.filter(date=date_filter)
    
    # Sorting
    sort_by = request.GET.get('sort_by', '-created_at')
    sort_order = request.GET.get('sort_order', 'desc')
    
    # Validate sort field to prevent injection
    allowed_sort_fields = ['id', 'date', 'start_time', 'duration_hours', 'total_amount', 'status', 'created_at', 'user__username']
    if sort_by.lstrip('-') in allowed_sort_fields:
        if sort_order == 'asc' and sort_by.startswith('-'):
            sort_by = sort_by[1:]
        elif sort_order == 'desc' and not sort_by.startswith('-'):
            sort_by = '-' + sort_by
        reservations = reservations.order_by(sort_by)
    else:
        reservations = reservations.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(reservations, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'staff/reservations.html', {
        'reservations': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'search_query': search_query,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'sort_by': sort_by,
        'sort_order': sort_order,
    })


@login_required
@staff_or_admin_required
def approve_reservation_view(request, reservation_id):
    
    res_qs = Reservation.objects.all()
    if request.user.organization:
        res_qs = res_qs.filter(court__organization=request.user.organization)
    reservation = get_object_or_404(res_qs, id=reservation_id)
    
    if request.method == 'POST':
        form = ReservationApprovalForm(request.POST, instance=reservation)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.approved_by = request.user
            reservation.approved_at = timezone.now()
            reservation.save()
            
            # Notify user
            Notification.objects.create(
                user=reservation.user,
                message=f"Your reservation #{reservation.id} has been {reservation.status}."
            )
            
            messages.success(request, f'Reservation #{reservation.id} has been {reservation.status}.')
            return redirect('staff_reservations')
    else:
        form = ReservationApprovalForm(instance=reservation)
    
    return render(request, 'admin/reservations/approve_reservation.html', {
        'form': form,
        'reservation': reservation
    })


@login_required
@user_required
def cancel_reservation_view(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)

    if reservation.status in ['completed', 'cancelled']:
        messages.error(request, 'This reservation cannot be cancelled.')
        return redirect('reservation_list')

    # Get active cancellation policy
    cancellation_policy = CancellationPolicy.objects.filter(is_active=True).first()
    if not cancellation_policy:
        # Create default policy if none exists
        cancellation_policy = CancellationPolicy.objects.create(
            name='Default Cancellation Policy',
            time_limit_minutes=20,
            deduction_percentage=30,
            is_active=True
        )

    # Check if cancellation is within time limit
    time_since_creation = timezone.now() - reservation.created_at
    time_limit_minutes = cancellation_policy.time_limit_minutes
    is_within_time_limit = time_since_creation <= timedelta(minutes=time_limit_minutes)

    if not is_within_time_limit:
        messages.error(request, f'Cancellation is only allowed within {time_limit_minutes} minutes of reservation creation. Your reservation was created {time_since_creation.total_seconds() / 60:.1f} minutes ago.')
        return redirect('reservation_list')

    if request.method == 'POST':
        form = CancellationRequestForm(request.POST)
        if form.is_valid():
            cancellation = form.save(commit=False)
            cancellation.reservation = reservation
            cancellation.requested_by = request.user
            cancellation.is_within_time_limit = is_within_time_limit

            # Calculate deduction based on policy
            deduction_percentage = cancellation_policy.deduction_percentage
            deduction_amount = (reservation.total_amount * deduction_percentage) / 100
            refund_amount = reservation.total_amount - deduction_amount

            cancellation.deduction_percentage = deduction_percentage
            cancellation.deduction_amount = deduction_amount
            cancellation.cancellation_note = f'A {deduction_percentage}% cancellation fee (₱{deduction_amount:,.2f}) has been applied. Refund amount: ₱{refund_amount:,.2f}.'
            cancellation.save()

            # Update reservation status
            reservation.status = 'cancelled'
            reservation.save()

            # Update payment status to refunded
            try:
                payment = reservation.payment
                if payment.status == 'paid':
                    payment.status = 'refunded'
                    payment.save()

                    # Create refund record with deducted amount
                    from payments.models import Refund
                    Refund.objects.create(
                        payment=payment,
                        amount=refund_amount,
                        reason=f"{cancellation.reason} ({deduction_percentage}% cancellation fee applied)",
                        status='processed',
                        requested_by=request.user
                    )
            except:
                pass

            # Return equipment
            for rental in reservation.rented_equipment.all():
                rental.equipment.quantity_available += rental.quantity
                rental.equipment.save()

            # Notify staff
            from accounts.models import User
            staff_users = User.objects.filter(role__in=['staff', 'admin'])
            for staff in staff_users:
                Notification.objects.create(
                    user=staff,
                    message=f"Reservation #{reservation.id} has been cancelled by {request.user.username} with {deduction_percentage}% deduction."
                )

            # Format success message with refund details
            refund_method_display = dict(cancellation.REFUND_METHOD_CHOICES).get(cancellation.refund_method, 'GCash')
            processing_time = "5-7 business days" if cancellation.refund_method == 'card' else "24-48 hours"

            success_message = (
                f"Booking #{reservation.id:06d} has been cancelled successfully. "
                f"A {deduction_percentage}% cancellation fee (₱{deduction_amount:,.2f}) has been applied. "
                f"Refund of ₱{refund_amount:,.2f} will be processed via {refund_method_display} "
                f"within {processing_time}."
            )

            messages.success(request, success_message)
            return redirect('reservation_list')
    else:
        form = CancellationRequestForm()

    # Calculate deduction amounts for display
    deduction_percentage = cancellation_policy.deduction_percentage
    deduction_amount = (reservation.total_amount * deduction_percentage) / 100
    refund_amount = reservation.total_amount - deduction_amount

    return render(request, 'user/cancel_reservation.html', {
        'form': form,
        'reservation': reservation,
        'is_within_time_limit': is_within_time_limit,
        'time_limit_minutes': time_limit_minutes,
        'time_remaining': timedelta(minutes=time_limit_minutes) - time_since_creation if is_within_time_limit else None,
        'deduction_percentage': deduction_percentage,
        'deduction_amount': deduction_amount,
        'refund_amount': refund_amount,
    })


@login_required
def calendar_view(request):
    # Get current month and year
    month = int(request.GET.get('month', timezone.now().month))
    year = int(request.GET.get('year', timezone.now().year))
    
    # Calculate calendar data
    import calendar
    cal = calendar.Calendar(calendar.SUNDAY)
    month_days = cal.monthdayscalendar(year, month)
    
    # Get reservations for this month
    if request.user.is_normal_user():
        reservations = Reservation.objects.filter(
            user=request.user,
            date__year=year,
            date__month=month,
            status__in=['confirmed', 'pending']
        )
    else:
        reservations = Reservation.objects.filter(
            date__year=year,
            date__month=month,
            status__in=['confirmed', 'pending']
        )
        # Org-scoping for org_admin and org_staff
        if request.user.organization:
            reservations = reservations.filter(court__organization=request.user.organization)
    
    # Group reservations by date
    reservation_dict = {}
    for res in reservations:
        day = res.date.day
        if day not in reservation_dict:
            reservation_dict[day] = []
        reservation_dict[day].append(res)

    # Create a list of days with reservations for easier template access
    days_with_reservations = list(reservation_dict.keys())

    month_name = calendar.month_name[month]

    return render(request, 'admin/reservations/reservation_calendar.html', {
        'month_days': month_days,
        'month_name': month_name,
        'year': year,
        'month': month,
        'reservations': reservation_dict,
        'days_with_reservations': days_with_reservations,
        'prev_month': month - 1 if month > 1 else 12,
        'next_month': month + 1 if month < 12 else 1,
        'prev_year': year if month > 1 else year - 1,
        'next_year': year if month < 12 else year + 1,
    })


# Admin CRUD Views

@login_required
@admin_required
def admin_reservation_list_view(request):

    reservations = Reservation.objects.select_related('user', 'court').all().order_by('-created_at')
    
    # Org-scoping for org_admin users
    if request.user.is_org_admin() and request.user.organization:
        reservations = reservations.filter(court__organization=request.user.organization)

    search_query = request.GET.get('search', '').strip()
    if search_query:
        reservations = reservations.filter(
            Q(id__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(court__name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        reservations = reservations.filter(status=status_filter)

    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        reservations = reservations.filter(date__gte=date_from)
    if date_to:
        reservations = reservations.filter(date__lte=date_to)

    # Sorting
    sort_by = request.GET.get('sort_by', '-created_at')
    sort_order = request.GET.get('sort_order', 'desc')
    allowed_sort_fields = ['id', 'date', 'duration_hours', 'total_amount', 'status', 'created_at', 'user__username', 'court__name']
    if sort_by.lstrip('-') in allowed_sort_fields:
        if sort_order == 'asc' and sort_by.startswith('-'):
            sort_by = sort_by[1:]
        elif sort_order == 'desc' and not sort_by.startswith('-'):
            sort_by = '-' + sort_by
        reservations = reservations.order_by(sort_by)

    # Pagination
    paginator = Paginator(reservations, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/reservations/reservation_list.html', {
        'reservations': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'search_query': search_query,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'sort_by': sort_by,
        'sort_order': sort_order,
    })


@login_required
@admin_required
def admin_reservation_create_view(request):

    if request.method == 'POST':
        form = AdminReservationForm(request.POST)
        # Filter court choices for org_admin BEFORE validation to prevent cross-org submissions
        if request.user.is_org_admin() and request.user.organization:
            form.fields['court'].queryset = Court.objects.filter(organization=request.user.organization, is_active=True)
        if form.is_valid():
            reservation = form.save(commit=False)
            # Set user if not provided
            if not reservation.user:
                reservation.user = request.user
            # Calculate totals with proper None handling
            hourly_rate = float(reservation.hourly_rate) if reservation.hourly_rate else 0.0
            duration_hours = float(reservation.duration_hours) if reservation.duration_hours else 0.0
            reservation.subtotal = hourly_rate * duration_hours
            reservation.total_amount = reservation.calculate_total()
            reservation.save()

            # Create payment record
            Payment.objects.create(
                reservation=reservation,
                amount=reservation.total_amount,
                status='pending'
            )

            messages.success(request, f'Reservation #{reservation.id} created successfully.')
            return redirect('admin_reservation_list')
    else:
        form = AdminReservationForm()
        # Filter court choices for org_admin on GET for the dropdown
        if request.user.is_org_admin() and request.user.organization:
            form.fields['court'].queryset = Court.objects.filter(organization=request.user.organization, is_active=True)

    return render(request, 'admin/reservations/reservation_form.html', {
        'form': form,
        'edit_mode': False,
    })


@login_required
@admin_required
def admin_reservation_edit_view(request, reservation_id):

    res_qs = Reservation.objects.all()
    # Org-scoping for org_admin
    if request.user.is_org_admin() and request.user.organization:
        res_qs = res_qs.filter(court__organization=request.user.organization)
    reservation = get_object_or_404(res_qs, id=reservation_id)
    if request.method == 'POST':
        form = AdminReservationForm(request.POST, instance=reservation)
        if form.is_valid():
            updated_reservation = form.save(commit=False)
            # Recalculate totals
            updated_reservation.subtotal = float(updated_reservation.hourly_rate) * float(updated_reservation.duration_hours)
            updated_reservation.total_amount = updated_reservation.calculate_total()
            updated_reservation.save()

            messages.success(request, f'Reservation #{reservation.id} updated successfully.')
            return redirect('admin_reservation_list')
    else:
        form = AdminReservationForm(instance=reservation)

    return render(request, 'admin/reservations/reservation_form.html', {
        'form': form,
        'edit_mode': True,
        'reservation': reservation,
    })


@login_required
@admin_required
def admin_reservation_delete_view(request, reservation_id):

    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('admin_reservation_list')

    res_qs = Reservation.objects.all()
    # Org-scoping for org_admin
    if request.user.is_org_admin() and request.user.organization:
        res_qs = res_qs.filter(court__organization=request.user.organization)
    reservation = get_object_or_404(res_qs, id=reservation_id)

    if reservation.status == 'cancelled':
        messages.info(request, f'Reservation #{reservation.id} is already cancelled.')
        return redirect('admin_reservation_list')

    # Return equipment if any
    for rental in reservation.rented_equipment.all():
        rental.equipment.quantity_available += rental.quantity
        rental.equipment.save()

    # Update reservation status
    reservation.status = 'cancelled'
    reservation.save(update_fields=['status'])

    # Update related payment
    Payment.objects.filter(reservation=reservation).update(status='cancelled')

    messages.success(request, f'Reservation #{reservation.id} cancelled successfully.')
    return redirect('admin_reservation_list')


@login_required
def get_time_slots_api(request):
    """API endpoint to get available time slots for a court and date."""
    court_id = request.GET.get('court_id')
    date_str = request.GET.get('date')

    if not court_id or not date_str:
        return JsonResponse({'error': 'Court ID and date are required'}, status=400)

    try:
        court = Court.objects.get(id=court_id, is_active=True)
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except Court.DoesNotExist:
        return JsonResponse({'error': 'Court not found'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    slots = court.get_time_slots(date)

    # Convert time objects to strings for JSON serialization
    serializable_slots = []
    for slot in slots:
        serializable_slots.append({
            'start': slot['start'],
            'end': slot['end'],
            'available': slot['available'],
            'label': slot['label']
        })

    return JsonResponse({'slots': serializable_slots})


@login_required
def get_monthly_availability_api(request):
    """API endpoint to check which dates in a month have available slots."""
    court_id = request.GET.get('court_id')
    month = int(request.GET.get('month', timezone.now().month))
    year = int(request.GET.get('year', timezone.now().year))

    if not court_id:
        return JsonResponse({'error': 'Court ID is required'}, status=400)

    try:
        court = Court.objects.get(id=court_id, is_active=True)
    except Court.DoesNotExist:
        return JsonResponse({'error': 'Court not found'}, status=404)

    import calendar
    cal = calendar.Calendar()
    month_days = [d for d in cal.itermonthdates(year, month) if d.month == month]

    # Get reservations for this court and month
    from .models import Reservation
    reservations = Reservation.objects.filter(
        court=court,
        date__year=year,
        date__month=month,
        status__in=['confirmed', 'pending']
    ).values_list('date', flat=True).distinct()

    # Skip past dates and check availability for future dates
    today = timezone.now().date()
    availability = {}
    for d in month_days:
        if d < today:
            availability[d.isoformat()] = 'past'
        else:
            slots = court.get_time_slots(d)
            has_available = any(s['available'] for s in slots)
            availability[d.isoformat()] = 'available' if has_available else 'full'

    return JsonResponse({
        'availability': availability,
        'month': month,
        'year': year,
        'month_name': calendar.month_name[month],
        'today': today.isoformat(),
    })


@login_required
def verify_slot_api(request):
    """API endpoint to verify a specific time slot is still available.
    Called inline before allowing user to proceed to confirmation step."""
    court_id = request.GET.get('court_id')
    date_str = request.GET.get('date')
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')

    if not all([court_id, date_str, start_str, end_str]):
        return JsonResponse({'available': False, 'message': 'Missing required parameters.'}, status=400)

    try:
        court = Court.objects.get(id=court_id, is_active=True)
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start = datetime.strptime(start_str, '%H:%M').time()
        end = datetime.strptime(end_str, '%H:%M').time()
    except (Court.DoesNotExist, ValueError):
        return JsonResponse({'available': False, 'message': 'Invalid court or date/time format.'}, status=400)

    # Check if slot is in the past
    slot_datetime = timezone.make_aware(datetime.combine(date, start))
    if slot_datetime < timezone.now():
        return JsonResponse({'available': False, 'message': 'This time slot has already passed.'})

    # Check for overlapping reservations
    from .models import Reservation
    overlapping = Reservation.objects.filter(
        court=court,
        date=date,
        status__in=['confirmed', 'pending']
    ).exclude(
        start_time__gte=end
    ).exclude(
        end_time__lte=start
    )

    if overlapping.exists():
        return JsonResponse({
            'available': False,
            'message': 'Sorry, this time slot was just booked by another user. Please select a different slot.'
        })

    return JsonResponse({'available': True, 'message': 'Slot is available.'})
