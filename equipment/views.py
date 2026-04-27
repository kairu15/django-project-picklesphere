from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from .models import Equipment, EquipmentRental, EquipmentMaintenance
from reservations.models import Reservation
from .forms import EquipmentForm
from datetime import timedelta


def equipment_list_view(request):
    equipment = Equipment.objects.filter(is_active=True)

    # Filter by type
    type_filter = request.GET.get('type', '')
    if type_filter:
        equipment = equipment.filter(type=type_filter)

    # Filter availability
    available_only = request.GET.get('available', '')
    if available_only:
        equipment = equipment.filter(quantity_available__gt=0)

    return render(request, 'user/equipment/equipment_list.html', {
        'equipment': equipment,
        'type_filter': type_filter,
        'available_only': available_only
    })


@login_required
def equipment_rental_create_view(request):
    if request.method == 'POST':
        equipment_id = request.POST.get('equipment_id')
        rental_days = int(request.POST.get('rental_days', 1))
        quantity = int(request.POST.get('quantity', 1))

        equipment = get_object_or_404(Equipment, id=equipment_id, is_active=True)

        if equipment.quantity_available < quantity:
            messages.error(request, 'Not enough equipment available.')
            return redirect('equipment_detail', equipment_id=equipment_id)

        rental_fee = equipment.rental_price * rental_days * quantity
        reserved_date = timezone.now().date()

        rental = EquipmentRental.objects.create(
            equipment=equipment,
            rented_by=request.user,
            reserved_date=reserved_date,
            rental_fee=rental_fee,
            status='reserved'
        )

        messages.success(request, f'Successfully reserved {equipment.name}.')
        return redirect('equipment_list')

    return redirect('equipment_list')


@login_required
def equipment_detail_view(request, equipment_id):
    equipment = get_object_or_404(Equipment, id=equipment_id, is_active=True)
    
    # Get rental history for staff/admin
    rental_history = None
    if request.user.is_staff_user() or request.user.is_admin():
        rental_history = EquipmentRental.objects.filter(equipment=equipment).order_by('-created_at')[:10]
    
    return render(request, 'user/equipment/equipment_detail.html', {
        'equipment': equipment,
        'rental_history': rental_history
    })


@login_required
def staff_equipment_view(request):
    if not request.user.is_staff_user() and not request.user.is_admin():
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')
    
    equipment = Equipment.objects.all().order_by('type', 'name')
    
    # Equipment statistics
    stats = {
        'total_items': Equipment.objects.filter(is_active=True).aggregate(
            total=Count('id')
        )['total'],
        'low_stock': Equipment.objects.filter(quantity_available__lte=2, is_active=True).count(),
        'out_of_stock': Equipment.objects.filter(quantity_available=0, is_active=True).count(),
        'active_rentals': EquipmentRental.objects.filter(status__in=['reserved', 'rented']).count(),
    }
    
    return render(request, 'staff/equipment.html', {
        'equipment': equipment,
        'stats': stats
    })


@login_required
def check_out_equipment_view(request, rental_id):
    if not request.user.is_staff_user() and not request.user.is_admin():
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('dashboard')
    
    rental = get_object_or_404(EquipmentRental, id=rental_id, status='reserved')
    
    if request.method == 'POST':
        rental.status = 'rented'
        rental.rented_at = timezone.now()
        rental.checked_out_by = request.user
        rental.condition_out = request.POST.get('condition_out', rental.equipment.condition)
        rental.save()
        
        # Update equipment quantity
        equipment = rental.equipment
        equipment.quantity_reserved -= 1
        equipment.quantity_available -= 1
        equipment.save()
        
        messages.success(request, f'{rental.equipment.name} checked out successfully.')
        return redirect('staff_equipment')
    
    return render(request, 'staff/equipment/check_out.html', {'rental': rental})


@login_required
def check_in_equipment_view(request, rental_id):
    if not request.user.is_staff_user() and not request.user.is_admin():
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('dashboard')
    
    rental = get_object_or_404(EquipmentRental, id=rental_id, status='rented')
    
    if request.method == 'POST':
        from django.utils import timezone
        rental.status = 'returned'
        rental.returned_at = timezone.now()
        rental.checked_in_by = request.user
        rental.condition_in = request.POST.get('condition_in', rental.condition_out)
        rental.notes = request.POST.get('notes', '')
        rental.save()
        
        # Update equipment quantity
        equipment = rental.equipment
        equipment.quantity_available += 1
        equipment.save()
        
        # Check if equipment needs maintenance
        if rental.condition_in == 'poor' or rental.condition_in == 'fair':
            messages.warning(request, f'Equipment returned in {rental.condition_in} condition. Consider maintenance.')
        else:
            messages.success(request, f'{rental.equipment.name} checked in successfully.')
        
        return redirect('staff_equipment')
    
    return render(request, 'staff/equipment/check_in.html', {'rental': rental})


from django.utils import timezone


# Admin CRUD Views

@login_required
def admin_equipment_list_view(request):
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')

    equipment = Equipment.objects.all().order_by('-created_at')

    search_query = request.GET.get('search', '').strip()
    if search_query:
        equipment = equipment.filter(
            Q(name__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(type__icontains=search_query)
        )

    type_filter = request.GET.get('type', '')
    if type_filter:
        equipment = equipment.filter(type=type_filter)

    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        equipment = equipment.filter(is_active=True)
    elif status_filter == 'inactive':
        equipment = equipment.filter(is_active=False)

    return render(request, 'admin/equipment/equipment_list.html', {
        'equipment': equipment,
        'search_query': search_query,
        'type_filter': type_filter,
        'status_filter': status_filter,
    })


@login_required
def admin_equipment_create_view(request):
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = EquipmentForm(request.POST, request.FILES)
        if form.is_valid():
            created_equipment = form.save()
            messages.success(request, f'Equipment {created_equipment.name} created successfully.')
            return redirect('admin_equipment_list')
    else:
        form = EquipmentForm()

    return render(request, 'admin/equipment/equipment_form.html', {
        'form': form,
        'edit_mode': False,
    })


@login_required
def admin_equipment_edit_view(request, equipment_id):
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')

    equipment = get_object_or_404(Equipment, id=equipment_id)
    if request.method == 'POST':
        form = EquipmentForm(request.POST, request.FILES, instance=equipment)
        if form.is_valid():
            form.save()
            messages.success(request, f'Equipment {equipment.name} updated successfully.')
            return redirect('admin_equipment_list')
    else:
        form = EquipmentForm(instance=equipment)

    return render(request, 'admin/equipment/equipment_form.html', {
        'form': form,
        'edit_mode': True,
        'equipment': equipment,
    })


@login_required
def admin_equipment_delete_view(request, equipment_id):
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('dashboard')

    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('admin_equipment_list')

    equipment = get_object_or_404(Equipment, id=equipment_id)
    if not equipment.is_active:
        messages.info(request, f'Equipment {equipment.name} is already inactive.')
        return redirect('admin_equipment_list')

    equipment.is_active = False
    equipment.save(update_fields=['is_active'])
    messages.success(request, f'Equipment {equipment.name} deactivated successfully.')
    return redirect('admin_equipment_list')
