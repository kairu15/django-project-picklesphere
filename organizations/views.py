from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from accounts.decorators import super_admin_required, org_admin_required, org_staff_or_admin_required, org_required
from .models import Organization
from .forms import OrganizationRegistrationForm, OrganizationProfileForm, OrganizationApprovalForm


# ==================== PUBLIC VIEWS ====================

def organization_directory(request):
    """Public directory of all approved organizations"""
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
    
    return render(request, 'public/organizations/organization_directory.html', {
        'organizations': organizations,
        'search_query': search_query,
        'city': city,
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
    """Super admin list of all organizations"""
    organizations = Organization.objects.all().order_by('-created_at')
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        organizations = organizations.filter(status=status_filter)
    
    search_query = request.GET.get('search', '')
    if search_query:
        organizations = organizations.filter(
            Q(name__icontains=search_query) |
            Q(contact_email__icontains=search_query)
        )
    
    # Stats
    stats = {
        'total': Organization.objects.count(),
        'pending': Organization.objects.filter(status='pending').count(),
        'approved': Organization.objects.filter(status='approved').count(),
        'suspended': Organization.objects.filter(status='suspended').count(),
    }
    
    return render(request, 'admin/organizations/organization_list.html', {
        'organizations': organizations,
        'stats': stats,
        'status_filter': status_filter,
        'search_query': search_query,
    })


@login_required
@super_admin_required
def super_admin_organization_detail(request, pk):
    """Super admin view of a single organization"""
    organization = get_object_or_404(Organization, pk=pk)
    courts = organization.courts.all()
    tournaments = organization.tournaments.all()
    staff_members = organization.members.filter(role__in=['org_admin', 'org_staff'])
    users = organization.members.filter(role='user')
    
    return render(request, 'admin/organizations/organization_detail.html', {
        'organization': organization,
        'courts': courts,
        'tournaments': tournaments,
        'staff_members': staff_members,
        'users': users,
    })


@login_required
@super_admin_required
def super_admin_approve_organization(request, pk):
    """Approve, reject, or suspend an organization"""
    organization = get_object_or_404(Organization, pk=pk)
    
    if request.method == 'POST':
        form = OrganizationApprovalForm(request.POST, instance=organization)
        if form.is_valid():
            old_status = organization.status
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
