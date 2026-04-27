from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Reservation, ReservationEquipment, CancellationRequest
from .forms import ReservationForm, ReservationApprovalForm, CancellationRequestForm, AdminReservationForm
from payments.models import Payment
from notifications.models import Notification
from equipment.models import Equipment
from accounts.models import User


@login_required
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
def reservation_create_view(request):
    if request.method == 'POST':
        form = ReservationForm(request.POST, user=request.user)
        equipment_ids = request.POST.getlist('equipment')
        
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.hourly_rate = reservation.court.hourly_rate
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
            
            # Notify staff
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
        form = ReservationForm(user=request.user)
    
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
def staff_reservations_view(request):
    if not request.user.is_staff_user() and not request.user.is_admin():
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')
    
    reservations = Reservation.objects.select_related('user', 'court', 'court__site', 'payment').all().order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        reservations = reservations.filter(status=status_filter)
    
    # Filter by date
    date_filter = request.GET.get('date', '')
    if date_filter:
        reservations = reservations.filter(date=date_filter)
    
    return render(request, 'staff/reservations.html', {
        'reservations': reservations,
        'status_filter': status_filter,
        'date_filter': date_filter
    })


@login_required
def approve_reservation_view(request, reservation_id):
    if not request.user.is_staff_user() and not request.user.is_admin():
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('dashboard')
    
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
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
def cancel_reservation_view(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    
    if reservation.status in ['completed', 'cancelled']:
        messages.error(request, 'This reservation cannot be cancelled.')
        return redirect('reservation_list')
    
    if request.method == 'POST':
        form = CancellationRequestForm(request.POST)
        if form.is_valid():
            cancellation = form.save(commit=False)
            cancellation.reservation = reservation
            cancellation.requested_by = request.user
            cancellation.save()
            
            # Update reservation status
            reservation.status = 'cancelled'
            reservation.save()
            
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
                    message=f"Reservation #{reservation.id} has been cancelled by {request.user.username}."
                )
            
            messages.success(request, 'Cancellation request submitted successfully.')
            return redirect('reservation_list')
    else:
        form = CancellationRequestForm()
    
    return render(request, 'user/cancel_reservation.html', {
        'form': form,
        'reservation': reservation
    })


@login_required
def calendar_view(request):
    # Get current month and year
    month = int(request.GET.get('month', timezone.now().month))
    year = int(request.GET.get('year', timezone.now().year))
    
    # Calculate calendar data
    import calendar
    cal = calendar.Calendar()
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
    
    # Group reservations by date
    reservation_dict = {}
    for res in reservations:
        day = res.date.day
        if day not in reservation_dict:
            reservation_dict[day] = []
        reservation_dict[day].append(res)
    
    month_name = calendar.month_name[month]
    
    return render(request, 'admin/reservations/reservation_calendar.html', {
        'month_days': month_days,
        'month_name': month_name,
        'year': year,
        'month': month,
        'reservations': reservation_dict,
        'prev_month': month - 1 if month > 1 else 12,
        'next_month': month + 1 if month < 12 else 1,
        'prev_year': year if month > 1 else year - 1,
        'next_year': year if month < 12 else year + 1,
    })


# Admin CRUD Views

@login_required
def admin_reservation_list_view(request):
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')

    reservations = Reservation.objects.select_related('user', 'court').all().order_by('-created_at')

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

    return render(request, 'admin/reservations/reservation_list.html', {
        'reservations': reservations,
        'search_query': search_query,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
    })


@login_required
def admin_reservation_create_view(request):
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = AdminReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            # Calculate totals
            reservation.subtotal = float(reservation.hourly_rate) * float(reservation.duration_hours)
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

    return render(request, 'admin/reservations/reservation_form.html', {
        'form': form,
        'edit_mode': False,
    })


@login_required
def admin_reservation_edit_view(request, reservation_id):
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')

    reservation = get_object_or_404(Reservation, id=reservation_id)
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
def admin_reservation_delete_view(request, reservation_id):
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('dashboard')

    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('admin_reservation_list')

    reservation = get_object_or_404(Reservation, id=reservation_id)

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
