from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from urllib.parse import urlencode
from accounts.decorators import admin_required
from .models import Site, Court
from .forms import CourtForm, SiteForm
from reservations.models import Reservation
from datetime import datetime, timedelta


def court_list_view(request):
    from organizations.models import Organization

    courts = Court.objects.filter(is_active=True).select_related('site', 'organization')
    sites = Site.objects.filter(is_active=True)
    organizations = Organization.objects.filter(is_active=True)
    
    # ---- Filters ----
    site_id = request.GET.get('site', '')
    if site_id:
        courts = courts.filter(site_id=site_id)
    
    court_type = request.GET.get('type', '')
    if court_type:
        courts = courts.filter(court_type=court_type)
    
    org_slug = request.GET.get('org', '')
    if org_slug:
        courts = courts.filter(organization__slug=org_slug)
    
    date = request.GET.get('date', '')
    if date:
        try:
            selected_date = datetime.strptime(date, '%Y-%m-%d').date()
            reserved_ids = Reservation.objects.filter(
                date=selected_date,
                status__in=['confirmed', 'pending']
            ).values_list('court_id', flat=True)
            courts = courts.exclude(id__in=reserved_ids)
        except ValueError:
            pass
    
    search_query = request.GET.get('q', '').strip()
    if search_query:
        courts = courts.filter(
            Q(name__icontains=search_query) |
            Q(site__name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(organization__name__icontains=search_query)
        )
    
    amenities_filter = request.GET.get('amenities', '').strip()
    if amenities_filter:
        courts = courts.filter(amenities__contains=[amenities_filter])
    
    # ---- Sorting ----
    sort = request.GET.get('sort', 'name')
    sort_map = {
        'name': 'name',
        '-name': '-name',
        'price': 'hourly_rate',
        '-price': '-hourly_rate',
        '-created_at': '-created_at',
        'created_at': 'created_at',
    }
    courts = courts.order_by(sort_map.get(sort, 'name'))
    
    # ---- Pagination ----
    paginator = Paginator(courts, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Build query string for pagination (preserve filters, remove page)
    query_params = request.GET.copy()
    query_params.pop('page', None)
    query_string = '&' + query_params.urlencode() if query_params else ''

    return render(request, 'public/courts/court_list.html', {
        'courts': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'sites': sites,
        'organizations': organizations,
        'selected_site': site_id,
        'selected_type': court_type,
        'selected_org': org_slug,
        'selected_date': date,
        'search_query': search_query,
        'sort_by': sort,
        'query_string': query_string,
    })


def court_detail_view(request, court_id):
    court = get_object_or_404(Court.objects.select_related('site', 'organization'), id=court_id, is_active=True)
    
    # Gallery images
    gallery_images = court.images.all()[:6]
    
    # Operating hours
    operating_hours = court.availability.all().order_by('day_of_week')
    
    # Upcoming reservations
    today = datetime.now().date()
    upcoming_reservations = Reservation.objects.filter(
        court=court,
        date__gte=today,
        status__in=['confirmed', 'pending']
    ).order_by('date', 'start_time')[:10]
    
    # Related courts (same site or organization, excluding current)
    related_courts = Court.objects.filter(
        is_active=True
    ).filter(
        Q(site=court.site) | Q(organization=court.organization)
    ).exclude(
        id=court.id
    ).select_related('site', 'organization').distinct()[:3]
    
    # Time slots for today
    from datetime import time
    time_slots = []
    for hour in range(8, 22):
        slot_start = time(hour, 0)
        is_booked = upcoming_reservations.filter(
            start_time__lt=time(hour + 1, 0),
            end_time__gt=time(hour, 0)
        ).exists()
        time_slots.append({
            'start': f'{hour:02d}:00',
            'end': f'{hour+1:02d}:00',
            'label': f'{hour:02d}:00 – {hour+1:02d}:00',
            'is_available': not is_booked,
        })
    
    return render(request, 'public/courts/court_detail.html', {
        'court': court,
        'gallery_images': gallery_images,
        'operating_hours': operating_hours,
        'upcoming_reservations': upcoming_reservations,
        'related_courts': related_courts,
        'time_slots': time_slots,
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
            return redirect('org_admin_court_list')
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
            return redirect('org_admin_court_list')
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
        return redirect('org_admin_court_list')
    
    court_qs = Court.objects.all()
    # Org-scoping for org_admin
    if request.user.is_org_admin() and request.user.organization:
        court_qs = court_qs.filter(organization=request.user.organization)
    
    court = get_object_or_404(court_qs, id=court_id)
    
    if not court.is_active:
        messages.info(request, f'Court {court.name} is already inactive.')
        return redirect('org_admin_court_list')
    
    court.is_active = False
    court.save(update_fields=['is_active'])
    messages.success(request, f'Court {court.name} deactivated successfully.')
    return redirect('org_admin_court_list')


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
            return redirect('org_admin_site_list')
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
            return redirect('org_admin_site_list')
    else:
        form = SiteForm(instance=site)
    
    return render(request, 'admin/sites/site_form.html', {'form': form, 'edit_mode': True, 'site': site})


@login_required
@admin_required
def admin_site_delete_view(request, site_id):
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('org_admin_site_list')
    
    site_qs = Site.objects.all()
    # Org-scoping for org_admin
    if request.user.is_org_admin() and request.user.organization:
        site_qs = site_qs.filter(organization=request.user.organization)
    
    site = get_object_or_404(site_qs, id=site_id)
    site.delete()
    messages.success(request, f'Site {site.name} deleted successfully.')
    return redirect('org_admin_site_list')
