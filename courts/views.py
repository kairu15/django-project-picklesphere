from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from accounts.decorators import admin_required
from .models import Site, Court
from .forms import CourtForm, SiteForm
from reservations.models import Reservation
from datetime import datetime, timedelta


def court_list_view(request):
    courts = Court.objects.filter(is_active=True)
    sites = Site.objects.filter(is_active=True)
    
    # Filter by site
    site_id = request.GET.get('site', '')
    if site_id:
        courts = courts.filter(site_id=site_id)
    
    # Filter by type
    court_type = request.GET.get('type', '')
    if court_type:
        courts = courts.filter(court_type=court_type)
    
    # Filter by availability
    date = request.GET.get('date', '')
    if date:
        try:
            selected_date = datetime.strptime(date, '%Y-%m-%d').date()
            # Get courts that don't have reservations on this date
            reserved_court_ids = Reservation.objects.filter(
                date=selected_date,
                status__in=['confirmed', 'pending']
            ).values_list('court_id', flat=True)
            courts = courts.exclude(id__in=reserved_court_ids)
        except ValueError:
            pass
    
    return render(request, 'public/courts/court_list.html', {
        'courts': courts,
        'sites': sites,
        'selected_site': site_id,
        'selected_type': court_type,
        'selected_date': date
    })


def court_detail_view(request, court_id):
    court = get_object_or_404(Court, id=court_id, is_active=True)
    
    # Get upcoming reservations for this court
    today = datetime.now().date()
    upcoming_reservations = Reservation.objects.filter(
        court=court,
        date__gte=today,
        status__in=['confirmed', 'pending']
    ).order_by('date', 'start_time')[:10]
    
    return render(request, 'public/courts/court_detail.html', {
        'court': court,
        'upcoming_reservations': upcoming_reservations
    })


@login_required
def court_availability_view(request, court_id):
    court = get_object_or_404(Court, id=court_id, is_active=True)
    
    date_str = request.GET.get('date', '')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = datetime.now().date()
    else:
        selected_date = datetime.now().date()
    
    # Get reservations for the selected date
    reservations = Reservation.objects.filter(
        court=court,
        date=selected_date,
        status__in=['confirmed', 'pending']
    ).order_by('start_time')
    
    # Generate time slots (8 AM to 10 PM, 1-hour slots)
    time_slots = []
    start_hour = 8
    end_hour = 22
    
    for hour in range(start_hour, end_hour):
        slot_time = f"{hour:02d}:00"
        slot_end = f"{hour+1:02d}:00"
        
        # Check if this slot is reserved
        is_reserved = reservations.filter(
            start_time__lte=f"{hour:02d}:00",
            end_time__gt=f"{hour:02d}:00"
        ).exists()
        
        time_slots.append({
            'time': slot_time,
            'end_time': slot_end,
            'is_available': not is_reserved
        })
    
    return render(request, 'public/courts/availability.html', {
        'court': court,
        'selected_date': selected_date,
        'time_slots': time_slots
    })


@login_required
@admin_required
def admin_court_list_view(request):
    
    courts = Court.objects.select_related('site', 'organization').all().order_by('-created_at')
    
    # Org-scoping for org_admin users
    if request.user.is_org_admin() and request.user.organization:
        courts = courts.filter(organization=request.user.organization)
    
    search_query = request.GET.get('search', '').strip()
    if search_query:
        courts = courts.filter(
            Q(name__icontains=search_query) |
            Q(site__name__icontains=search_query) |
            Q(court_type__icontains=search_query) |
            Q(organization__name__icontains=search_query)
        )
    
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        courts = courts.filter(is_active=True)
    elif status_filter == 'inactive':
        courts = courts.filter(is_active=False)
    
    # Sorting
    sort_by = request.GET.get('sort_by', '-created_at')
    sort_order = request.GET.get('sort_order', 'desc')
    allowed_sort_fields = ['name', 'site__name', 'court_type', 'hourly_rate', 'created_at']
    if sort_by.lstrip('-') in allowed_sort_fields:
        if sort_order == 'asc' and sort_by.startswith('-'):
            sort_by = sort_by[1:]
        elif sort_order == 'desc' and not sort_by.startswith('-'):
            sort_by = '-' + sort_by
        courts = courts.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(courts, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin/courts/court_list.html', {
        'courts': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'search_query': search_query,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'sort_order': sort_order,
    })


@login_required
@admin_required
def admin_court_create_view(request):

    initial = {}
    
    # Auto-assign organization for org_admin users
    if request.user.is_org_admin() and request.user.organization:
        initial['organization'] = request.user.organization_id
    
    if request.method == 'POST':
        form = CourtForm(request.POST, request.FILES, initial=initial)
        if form.is_valid():
            created_court = form.save(commit=False)
            if request.user.is_org_admin() and request.user.organization:
                created_court.organization = request.user.organization
            created_court.save()
            messages.success(request, f'Court {created_court.name} created successfully.')
            return redirect('admin_court_list')
    else:
        form = CourtForm(initial=initial)
    
    # Filter site choices for org_admin
    if request.user.is_org_admin() and request.user.organization:
        form.fields['site'].queryset = Site.objects.filter(organization=request.user.organization)
    
    return render(request, 'admin/courts/court_form.html', {
        'form': form,
        'edit_mode': False,
    })


@login_required
@admin_required
def admin_court_edit_view(request, court_id):

    court_qs = Court.objects.all()
    # Org-scoping for org_admin
    if request.user.is_org_admin() and request.user.organization:
        court_qs = court_qs.filter(organization=request.user.organization)
    
    court = get_object_or_404(court_qs, id=court_id)

    if request.method == 'POST':
        form = CourtForm(request.POST, request.FILES, instance=court)
        if form.is_valid():
            form.save()
            messages.success(request, f'Court {court.name} updated successfully.')
            return redirect('admin_court_list')
    else:
        form = CourtForm(instance=court)

    return render(request, 'admin/courts/court_form.html', {
        'form': form,
        'edit_mode': True,
        'court': court,
    })


@login_required
@admin_required
def admin_court_delete_view(request, court_id):
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('admin_court_list')
    
    court_qs = Court.objects.all()
    # Org-scoping for org_admin
    if request.user.is_org_admin() and request.user.organization:
        court_qs = court_qs.filter(organization=request.user.organization)
    
    court = get_object_or_404(court_qs, id=court_id)
    
    if not court.is_active:
        messages.info(request, f'Court {court.name} is already inactive.')
        return redirect('admin_court_list')
    
    court.is_active = False
    court.save(update_fields=['is_active'])
    messages.success(request, f'Court {court.name} deactivated successfully.')
    return redirect('admin_court_list')


@login_required
@admin_required
def admin_site_list_view(request):
    
    sites = Site.objects.all().order_by('-created_at')
    
    # Org-scoping for org_admin users
    if request.user.is_org_admin() and request.user.organization:
        sites = sites.filter(organization=request.user.organization)
    
    return render(request, 'admin/sites/site_list.html', {'sites': sites})


@login_required
@admin_required
def admin_site_create_view(request):
    
    if request.method == 'POST':
        form = SiteForm(request.POST)
        if form.is_valid():
            site = form.save(commit=False)
            # Auto-assign organization for org_admin
            if request.user.is_org_admin() and request.user.organization:
                site.organization = request.user.organization
            site.save()
            messages.success(request, 'Site created successfully.')
            return redirect('admin_site_list')
    else:
        form = SiteForm()
    
    return render(request, 'admin/sites/site_form.html', {'form': form, 'edit_mode': False})


@login_required
@admin_required
def admin_site_edit_view(request, site_id):
    
    site_qs = Site.objects.all()
    # Org-scoping for org_admin
    if request.user.is_org_admin() and request.user.organization:
        site_qs = site_qs.filter(organization=request.user.organization)
    
    site = get_object_or_404(site_qs, id=site_id)
    if request.method == 'POST':
        form = SiteForm(request.POST, instance=site)
        if form.is_valid():
            form.save()
            messages.success(request, f'Site {site.name} updated successfully.')
            return redirect('admin_site_list')
    else:
        form = SiteForm(instance=site)
    
    return render(request, 'admin/sites/site_form.html', {'form': form, 'edit_mode': True, 'site': site})


@login_required
@admin_required
def admin_site_delete_view(request, site_id):
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('admin_site_list')
    
    site_qs = Site.objects.all()
    # Org-scoping for org_admin
    if request.user.is_org_admin() and request.user.organization:
        site_qs = site_qs.filter(organization=request.user.organization)
    
    site = get_object_or_404(site_qs, id=site_id)
    site.delete()
    messages.success(request, f'Site {site.name} deleted successfully.')
    return redirect('admin_site_list')
