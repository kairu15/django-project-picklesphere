from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from accounts.decorators import super_admin_required, org_admin_required, org_staff_or_admin_required, org_required
from .models import Organization
from .forms import OrganizationRegistrationForm, OrganizationProfileForm, OrganizationApprovalForm, SuperAdminOrganizationForm, OrgStaffAssignmentForm
from accounts.models import User
from django.core.paginator import Paginator


# ==================== PUBLIC VIEWS ====================

def organization_directory(request):
    """Public directory of all approved organizations"""
    from dashboard.models import OrganizationPageSettings, FeaturedOrganization, OrganizationCategory
    
    organizations = Organization.objects.filter(status='approved', is_active=True)
    
    search_query = request.GET.get('search', '')
    if search_query:
        organizations = organizations.filter(
            Q(name__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(province__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    city = request.GET.get('city', '')
    if city:
        organizations = organizations.filter(city__icontains=city)
    
    # CMS Data
    cms_settings = OrganizationPageSettings.objects.first()
    featured_organizations = FeaturedOrganization.objects.filter(is_active=True).select_related('organization').order_by('display_order')[:6]
    categories = OrganizationCategory.objects.filter(is_active=True).order_by('display_order')
    
    return render(request, 'public/organizations/organization_directory.html', {
        'organizations': organizations,
        'search_query': search_query,
        'city': city,
        'cms_settings': cms_settings,
        'featured_organizations': featured_organizations,
        'categories': categories,
    })


def organization_public_detail(request, slug):
    """Public detail page for an organization"""
    organization = get_object_or_404(Organization, slug=slug, status='approved', is_active=True)
    courts = organization.courts.filter(is_active=True)
    tournaments = organization.tournaments.filter(status__in=['registration_open', 'in_progress', 'draft'])
    
    return render(request, 'public/organizations/organization_detail.html', {
        'organization': organization,
        'courts': courts,
        'tournaments': tournaments,
    })


def organization_register(request):
    """Public registration form for new organizations"""
    if request.method == 'POST':
        form = OrganizationRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            org = form.save()
            messages.success(request, 
                'Your organization has been registered successfully! '
                'A super admin will review your application and approve it shortly. '
                'You will be notified once your organization is approved.')
            return redirect('home')
    else:
        form = OrganizationRegistrationForm()
    
    return render(request, 'public/organizations/organization_register.html', {
        'form': form,
    })


# ==================== SUPER ADMIN VIEWS ====================

@login_required
@super_admin_required
def super_admin_organization_list(request):
    """Super admin list of all organizations with full management controls"""
    from reservations.models import Reservation
    
    organizations = Organization.objects.all().select_related('approved_by').annotate(
        court_count_prop=Count('courts', filter=Q(courts__is_active=True)),
        tournament_count_prop=Count('tournaments'),
        reservation_count_prop=Count('courts__reservations', filter=~Q(courts__reservations__status='cancelled')),
    )
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        organizations = organizations.filter(
            Q(name__icontains=search_query) |
            Q(contact_email__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(province__icontains=search_query)
        )
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        organizations = organizations.filter(status=status_filter)
    
    # Sorting
    sort_by = request.GET.get('sort_by', '-created_at')
    sort_order = request.GET.get('sort_order', 'desc')
    allowed_sort_fields = ['name', 'status', 'created_at', 'city', 'court_count_prop', 'tournament_count_prop', 'reservation_count_prop']
    if sort_by.lstrip('-') in allowed_sort_fields:
        if sort_order == 'asc' and sort_by.startswith('-'):
            sort_by = sort_by[1:]
        elif sort_order == 'desc' and not sort_by.startswith('-'):
            sort_by = '-' + sort_by
        organizations = organizations.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(organizations, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Stats - include all statuses
    stats = {
        'total': Organization.objects.count(),
        'pending': Organization.objects.filter(status='pending').count(),
        'approved': Organization.objects.filter(status='approved').count(),
        'rejected': Organization.objects.filter(status='rejected').count(),
        'suspended': Organization.objects.filter(status='suspended').count(),
    }
    
    # Annotate each org with its admin for the template
    org_list = page_obj.object_list
    org_admins = {}
    for org in org_list:
        admin = User.objects.filter(organization=org, role='org_admin').first()
        org_admins[org.id] = admin
    
    return render(request, 'admin/organizations/organization_list.html', {
        'organizations': org_list,
        'org_admins': org_admins,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'stats': stats,
        'status_filter': status_filter,
        'search_query': search_query,
        'sort_by': sort_by,
        'sort_order': sort_order,
    })


@login_required
@super_admin_required
def super_admin_organization_detail(request, pk):
    """Super admin view of a single organization"""
    from reservations.models import Reservation
    from payments.models import Payment
    
    organization = get_object_or_404(Organization, pk=pk)
    courts = organization.courts.all()
    tournaments = organization.tournaments.all()
    staff_members = organization.members.filter(role__in=['org_admin', 'org_staff'])
    users = organization.members.filter(role='user')
    org_admin_user = organization.members.filter(role='org_admin').first()
    
    # Stats
    court_ids = organization.courts.values_list('id', flat=True)
    reservation_count = Reservation.objects.filter(court_id__in=court_ids).exclude(status='cancelled').count()
    revenue = Payment.objects.filter(
        reservation__court_id__in=court_ids,
        status='paid'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    active_tournaments = organization.tournaments.filter(status__in=['registration_open', 'in_progress']).count()
    
    return render(request, 'admin/organizations/organization_detail.html', {
        'organization': organization,
        'courts': courts,
        'tournaments': tournaments,
        'staff_members': staff_members,
        'users': users,
        'org_admin_user': org_admin_user,
        'reservation_count': reservation_count,
        'revenue': revenue,
        'active_tournaments': active_tournaments,
        'total_tournaments': tournaments.count(),
    })


@login_required
@super_admin_required
def super_admin_approve_organization(request, pk):
    """Approve, reject, or suspend an organization"""
    organization = get_object_or_404(Organization, pk=pk)
    
    old_status = organization.status
    
    if request.method == 'POST':
        form = OrganizationApprovalForm(request.POST, instance=organization)
        if form.is_valid():
            org = form.save(commit=False)
            
            if org.status == 'approved' and old_status != 'approved':
                org.approved_by = request.user
                org.approved_at = timezone.now()
                messages.success(request, f'Organization "{org.name}" has been approved!')
            elif org.status == 'rejected':
                messages.info(request, f'Organization "{org.name}" has been rejected.')
            elif org.status == 'suspended':
                messages.warning(request, f'Organization "{org.name}" has been suspended.')
            else:
                messages.info(request, f'Organization "{org.name}" has been updated.')
            
            org.save()
            return redirect('super_admin_organization_list')
    else:
        form = OrganizationApprovalForm(instance=organization)
    
    return render(request, 'admin/organizations/organization_approve.html', {
        'form': form,
        'organization': organization,
    })


@login_required
@super_admin_required
def super_admin_toggle_org_status(request, pk):
    """Quick toggle to activate/deactivate an organization"""
    organization = get_object_or_404(Organization, pk=pk)
    
    if request.method == 'POST':
        organization.is_active = not organization.is_active
        organization.save()
        
        status = "activated" if organization.is_active else "deactivated"
        messages.success(request, f'Organization "{organization.name}" has been {status}.')
    
    return redirect('super_admin_organization_list')


@login_required
@super_admin_required
def super_admin_organization_create(request):
    """Super Admin creates a new organization with all details"""
    if request.method == 'POST':
        form = SuperAdminOrganizationForm(request.POST, request.FILES)
        if form.is_valid():
            org = form.save(commit=False)
            # If approving immediately, record approval
            if org.status == 'approved':
                org.approved_by = request.user
                org.approved_at = timezone.now()
            org.save()
            
            # Assign org admin if specified
            org_admin_user = form.cleaned_data.get('org_admin')
            if org_admin_user:
                org_admin_user.organization = org
                org_admin_user.save()
            
            messages.success(request, f'Organization "{org.name}" created successfully!')
            return redirect('super_admin_organization_list')
    else:
        form = SuperAdminOrganizationForm()
    
    return render(request, 'admin/organizations/organization_form.html', {
        'form': form,
        'edit_mode': False,
    })


@login_required
@super_admin_required
def super_admin_organization_edit(request, pk):
    """Super Admin edits an organization's full details"""
    organization = get_object_or_404(Organization, pk=pk)
    
    old_status = organization.status
    
    if request.method == 'POST':
        form = SuperAdminOrganizationForm(request.POST, request.FILES, instance=organization)
        if form.is_valid():
            org = form.save(commit=False)
            
            # If newly approved, record approval
            if org.status == 'approved' and old_status != 'approved':
                org.approved_by = request.user
                org.approved_at = timezone.now()
            
            org.save()
            
            # Handle org admin reassignment
            org_admin_user = form.cleaned_data.get('org_admin')
            current_admin = User.objects.filter(organization=org, role='org_admin').first()
            
            if org_admin_user:
                if current_admin and current_admin != org_admin_user:
                    # Unassign old admin
                    current_admin.organization = None
                    current_admin.save()
                # Assign new admin
                org_admin_user.organization = org
                org_admin_user.save()
            elif current_admin:
                # No admin selected, unassign current
                current_admin.organization = None
                current_admin.save()
            
            messages.success(request, f'Organization "{org.name}" updated successfully!')
            return redirect('super_admin_organization_list')
    else:
        form = SuperAdminOrganizationForm(instance=organization)
    
    return render(request, 'admin/organizations/organization_form.html', {
        'form': form,
        'edit_mode': True,
        'organization': organization,
    })


@login_required
@super_admin_required
def super_admin_organization_delete(request, pk):
    """Delete an organization with validation for active reservations/tournaments"""
    from reservations.models import Reservation
    from tournaments.models import Tournament
    from payments.models import Payment
    
    organization = get_object_or_404(Organization, pk=pk)
    
    # Check for active reservations
    org_court_ids = organization.courts.values_list('id', flat=True)
    active_reservation_statuses = ['pending', 'confirmed']
    active_reservations = Reservation.objects.filter(
        court_id__in=org_court_ids,
        status__in=active_reservation_statuses
    )
    active_reservation_count = active_reservations.count()
    
    # Check for active tournaments
    active_tournament_statuses = ['draft', 'registration_open', 'registration_closed', 'in_progress']
    active_tournaments = organization.tournaments.filter(
        status__in=active_tournament_statuses
    )
    active_tournament_count = active_tournaments.count()
    
    # Check for pending payments
    pending_payments = Payment.objects.filter(
        reservation__court_id__in=org_court_ids,
        status='pending'
    )
    pending_payment_count = pending_payments.count()
    
    has_active_data = (
        active_reservation_count > 0 or
        active_tournament_count > 0 or
        pending_payment_count > 0
    )
    
    if request.method == 'POST':
        if has_active_data:
            reasons = []
            if active_reservation_count:
                reasons.append(f'{active_reservation_count} active reservation(s)')
            if active_tournament_count:
                reasons.append(f'{active_tournament_count} active tournament(s)')
            if pending_payment_count:
                reasons.append(f'{pending_payment_count} pending payment(s)')
            messages.error(
                request,
                f'Cannot delete "{organization.name}": it has {", ".join(reasons)}. '
                'Please cancel or complete them before deleting the organization.'
            )
            return redirect('super_admin_organization_list')
        
        org_name = organization.name
        # Unassign all members
        User.objects.filter(organization=organization).update(organization=None)
        organization.delete()
        messages.success(request, f'Organization "{org_name}" has been permanently deleted.')
        return redirect('super_admin_organization_list')
    
    return render(request, 'admin/organizations/organization_confirm_delete.html', {
        'organization': organization,
        'active_reservations': active_reservations,
        'active_reservation_count': active_reservation_count,
        'active_tournaments': active_tournaments,
        'active_tournament_count': active_tournament_count,
        'pending_payment_count': pending_payment_count,
        'has_active_data': has_active_data,
    })


@login_required
@super_admin_required
def super_admin_dashboard(request):
    """Super Admin main dashboard with system-wide analytics"""
    from accounts.models import User
    from courts.models import Court
    from reservations.models import Reservation
    from tournaments.models import Tournament
    from payments.models import Payment
    
    today = timezone.now().date()
    
    # System-wide metrics
    metrics = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'total_organizations': Organization.objects.count(),
        'pending_organizations': Organization.objects.filter(status='pending').count(),
        'approved_organizations': Organization.objects.filter(status='approved').count(),
        'total_courts': Court.objects.filter(is_active=True).count(),
        'total_reservations': Reservation.objects.exclude(status='cancelled').count(),
        'today_reservations': Reservation.objects.filter(date=today).count(),
        'total_tournaments': Tournament.objects.count(),
        'active_tournaments': Tournament.objects.filter(status__in=['registration_open', 'in_progress']).count(),
    }
    
    # Revenue stats
    revenue_stats = {
        'total_revenue': Payment.objects.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0,
        'today_revenue': Payment.objects.filter(status='paid', created_at__date=today).aggregate(Sum('amount'))['amount__sum'] or 0,
        'pending_amount': Payment.objects.filter(status='pending').aggregate(Sum('amount'))['amount__sum'] or 0,
    }
    
    # ========== REVENUE TREND (last 14 days) ==========
    from datetime import timedelta
    fourteen_days_ago = today - timedelta(days=13)
    daily_revenues = Payment.objects.filter(
        status='paid',
        created_at__date__gte=fourteen_days_ago
    ).extra(
        select={'day': 'DATE(created_at)'}
    ).values('day').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('day')
    
    revenue_trend_labels = []
    revenue_trend_values = []
    booking_trend_values = []
    for i in range(13, -1, -1):
        day = today - timedelta(days=i)
        revenue_trend_labels.append(day.strftime('%b %d'))
        found = next((item for item in daily_revenues if item['day'] == day), None)
        revenue_trend_values.append(float(found['total'] or 0) if found else 0)
        booking_trend_values.append(found['count'] if found else 0)
    
    # Recent registrations (pending orgs)
    pending_orgs = Organization.objects.filter(status='pending').order_by('-created_at')[:10]
    
    # Organization stats
    org_stats = Organization.objects.filter(status='approved').annotate(
        total_courts=Count('courts'),
        total_tournaments=Count('tournaments'),
    ).order_by('-total_courts')[:10]
    
    return render(request, 'admin/organizations/super_admin_dashboard.html', {
        'metrics': metrics,
        'revenue_stats': revenue_stats,
        'pending_orgs': pending_orgs,
        'org_stats': org_stats,
        # Revenue trend
        'revenue_trend_labels': revenue_trend_labels,
        'revenue_trend_values': revenue_trend_values,
        'booking_trend_values': booking_trend_values,
    })


# ==================== ORG ADMIN VIEWS ====================

@login_required
@org_admin_required
@org_required
def org_admin_dashboard(request):
    """Organization Admin dashboard - scoped to their organization"""
    from reservations.models import Reservation
    from payments.models import Payment
    
    org = request.user.organization
    today = timezone.now().date()
    
    org_court_ids = org.courts.values_list('id', flat=True)
    
    # Org-specific metrics
    metrics = {
        'total_courts': org.courts.filter(is_active=True).count(),
        'active_tournaments': org.tournaments.filter(status__in=['registration_open', 'in_progress']).count(),
        'total_tournaments': org.tournaments.count(),
        'today_reservations': Reservation.objects.filter(court_id__in=org_court_ids, date=today).count(),
        'pending_reservations': Reservation.objects.filter(court_id__in=org_court_ids, status='pending').count(),
        'total_reservations': Reservation.objects.filter(court_id__in=org_court_ids).exclude(status='cancelled').count(),
        'staff_count': org.staff_count,
    }
    
    # Revenue
    org_revenue = Payment.objects.filter(
        reservation__court_id__in=org_court_ids,
        status='paid'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Recent reservations
    recent_reservations = Reservation.objects.filter(
        court_id__in=org_court_ids
    ).select_related('user', 'court').order_by('-created_at')[:10]
    
    return render(request, 'admin/organizations/org_admin_dashboard.html', {
        'organization': org,
        'metrics': metrics,
        'org_revenue': org_revenue,
        'recent_reservations': recent_reservations,
    })


@login_required
@org_admin_required
@org_required
def org_admin_manage_staff(request):
    """Organization Admin manages staff members for their organization."""
    org = request.user.organization

    # Get current staff (org_staff role, belonging to this org)
    staff_members = User.objects.filter(
        organization=org,
        role='org_staff'
    ).order_by('username')

    # Handle POST: add or remove staff
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            form = OrgStaffAssignmentForm(request.POST, org=org)
            if form.is_valid():
                user = form.cleaned_data['user']
                user.organization = org
                user.role = 'org_staff'
                user.save()
                staff_name = user.get_full_name() or user.username
                messages.success(
                    request,
                    f'"{staff_name}" has been added as a staff member.'
                )
                return redirect('org_admin_manage_staff')
            else:
                messages.error(request, 'Please select a valid user to add.')

        elif action == 'remove':
            user_id = request.POST.get('user_id')
            if user_id:
                user = get_object_or_404(User, id=user_id, organization=org, role='org_staff')
                username = user.get_full_name() or user.username
                user.organization = None
                user.role = 'user'
                user.save()
                messages.success(
                    request,
                    f'"{username}" has been removed from staff and is now a regular user.'
                )
                return redirect('org_admin_manage_staff')

        elif action == 'update_max':
            max_staff = request.POST.get('max_staff_accounts')
            if max_staff and max_staff.isdigit():
                val = int(max_staff)
                if 1 <= val <= 100:
                    org.max_staff_accounts = val
                    org.save(update_fields=['max_staff_accounts'])
                    messages.success(request, f'Maximum staff accounts updated to {val}.')
                else:
                    messages.error(request, 'Maximum staff accounts must be between 1 and 100.')
            return redirect('org_admin_manage_staff')

    else:
        form = OrgStaffAssignmentForm(org=org)

    # Get eligible regular users (role='user', no org affiliation or with this org only)
    eligible_users = User.objects.filter(
        role='user',
        is_active=True
    ).exclude(
        organization=org,
        role__in=['org_admin', 'org_staff']
    ).order_by('username')[:50]

    can_add = org.can_add_staff()
    staff_limit = org.max_staff_accounts

    return render(request, 'admin/organizations/org_admin_staff.html', {
        'organization': org,
        'staff_members': staff_members,
        'form': form,
        'eligible_users': eligible_users,
        'can_add': can_add,
        'staff_limit': staff_limit,
        'current_staff_count': staff_members.count(),
    })


@login_required
@org_admin_required
@org_required
def org_admin_profile(request):
    """Edit organization profile"""
    org = request.user.organization
    
    if request.method == 'POST':
        form = OrganizationProfileForm(request.POST, request.FILES, instance=org)
        if form.is_valid():
            form.save()
            messages.success(request, 'Organization profile updated successfully!')
            return redirect('org_admin_dashboard')
    else:
        form = OrganizationProfileForm(instance=org)
    
    return render(request, 'admin/organizations/org_admin_profile.html', {
        'form': form,
        'organization': org,
    })


def static_map_view(request):
    """Generate a static map image for a given lat/lng."""
    from staticmap import StaticMap, CircleMarker
    from io import BytesIO
    
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    width = int(request.GET.get('width', 300))
    height = int(request.GET.get('height', 180))
    zoom = int(request.GET.get('zoom', 15))
    
    if not lat or not lng:
        return HttpResponse(status=400)
    
    try:
        lat = float(lat)
        lng = float(lng)
    except (ValueError, TypeError):
        return HttpResponse(status=400)
    
    try:
        m = StaticMap(width, height, url_template='https://tile.openstreetmap.org/{z}/{x}/{y}.png')
        marker = CircleMarker((lng, lat), 'red', 8)
        m.add_marker(marker)
        image = m.render(zoom=zoom)
        
        buf = BytesIO()
        image.save(buf, format='PNG')
        buf.seek(0)
        
        response = HttpResponse(buf.getvalue(), content_type='image/png')
        # Cache for 24 hours
        response['Cache-Control'] = 'public, max-age=86400'
        return response
    except Exception as e:
        return HttpResponse(status=500)


@login_required
@org_admin_required
@org_required
def org_admin_location_setup(request):
    """Interactive map page for org admin to set facility location."""
    org = request.user.organization
    
    if request.method == 'POST':
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        address = request.POST.get('location_address', '').strip()
        city = request.POST.get('city', '').strip()
        province = request.POST.get('province', '').strip()
        
        if lat and lng:
            try:
                org.latitude = float(lat)
                org.longitude = float(lng)
                org.location_address = address or org.location_address
                if city:
                    org.city = city
                if province:
                    org.province = province
                org.save(update_fields=['latitude', 'longitude', 'location_address', 'city', 'province'])
                messages.success(request, 'Location saved successfully!')
                return redirect('org_admin_location_setup')
            except (ValueError, TypeError):
                messages.error(request, 'Invalid coordinates. Please place the pin on the map.')
        else:
            messages.error(request, 'Please place a pin on the map to set the location.')
    
    return render(request, 'admin/organizations/org_admin_location.html', {
        'organization': org,
        'org_lat': float(org.latitude) if org.latitude else None,
        'org_lng': float(org.longitude) if org.longitude else None,
        'org_address': org.location_address or '',
    })


@login_required
@org_admin_required
@org_required
def reverse_geocode_api(request):
    """Proxy endpoint for Nominatim reverse geocoding to avoid CORS issues."""
    import urllib.request, urllib.parse, json
    
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    
    if not lat or not lng:
        return JsonResponse({'error': 'lat and lng parameters required'}, status=400)
    
    try:
        params = urllib.parse.urlencode({
            'format': 'jsonv2',
            'lat': lat,
            'lon': lng,
            'addressdetails': 1,
        })
        url = f'https://nominatim.openstreetmap.org/reverse?{params}'
        req = urllib.request.Request(url, headers={
            'User-Agent': 'PickleSphere/1.0 (organization location picker)',
        })
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        if 'display_name' in data:
            address = data['display_name']
            # Also extract city/province if available
            addr_details = data.get('address', {})
            city = addr_details.get('city', addr_details.get('town', addr_details.get('village', '')))
            province = addr_details.get('state', addr_details.get('province', ''))
            return JsonResponse({
                'display_name': address,
                'city': city,
                'province': province,
                'lat': data.get('lat', lat),
                'lon': data.get('lon', lng),
            })
        else:
            return JsonResponse({'display_name': f'{lat}, {lng}', 'city': '', 'province': ''})
    except Exception as e:
        return JsonResponse({'display_name': f'{lat}, {lng}', 'city': '', 'province': '', 'error': str(e)})
