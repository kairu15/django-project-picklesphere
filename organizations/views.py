from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.db.models.functions import ExtractHour
from django.utils import timezone
from django.http import JsonResponse, HttpResponse, Http404
import csv
from django.core.paginator import Paginator
from datetime import timedelta

from accounts.decorators import super_admin_required, org_admin_required, org_staff_or_admin_required, org_required
from accounts.models import User, StaffPermission, UserActivity
from courts.models import Court
from dashboard.models import OrganizationPageSettings, FeaturedOrganization, OrganizationCategory
from reservations.models import Reservation
from tournaments.models import Tournament
from payments.models import Payment, Refund
from .models import Organization, OrganizationAuditLog
from .forms import (
    OrganizationRegistrationForm, OrganizationProfileForm,
    OrganizationApprovalForm, SuperAdminOrganizationForm,
    OrganizationVerificationForm,
    StaffAccountCreateForm, StaffEditForm, StaffPermissionForm
)
from notifications.utils import (
    notify_org_admin_org_status_change,
    notify_org_admin_org_verified,
    notify_super_admin_org_verified,
    notify_org_owned_users_org_status_change,
    notify_super_admin_new_organization,
)
import uuid

from notifications.email_utils import (
    send_org_registration_confirmation_email,
    send_org_status_change_email,
    send_org_admin_created_email,
    send_password_reset_email,
)
from django.template.response import TemplateResponse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


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
            # Notify all super admins about the new registration
            super_admins = User.objects.filter(role='super_admin', is_active=True)
            for sa in super_admins:
                notify_super_admin_new_organization(sa, org)
            # Send confirmation email
            send_org_registration_confirmation_email(request.user, org)
            
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


def _create_org_audit_log(organization, action, performed_by, details='', changes=None, request=None):
    """Helper to create an organization audit log entry."""
    OrganizationAuditLog.objects.create(
        organization=organization,
        action=action,
        performed_by=performed_by,
        details=details,
        changes=changes,
        ip_address=request.META.get('REMOTE_ADDR') if request else None,
    )


# ==================== SUPER ADMIN VIEWS ====================

@login_required
@super_admin_required
def super_admin_organization_list(request):
    """Super admin list of all organizations with full management controls"""
    
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
    """Approve, reject, or suspend an organization with notifications and audit logging."""
    organization = get_object_or_404(Organization, pk=pk)
    
    old_status = organization.status
    
    if request.method == 'POST':
        form = OrganizationApprovalForm(request.POST, instance=organization)
        if form.is_valid():
            org = form.save(commit=False)
            new_status = org.status
            
            # Build changes dict for audit log
            changes = {
                'old_status': old_status,
                'new_status': new_status,
            }
            
            if new_status == 'approved':
                if old_status != 'approved':
                    org.approved_by = request.user
                    org.approved_at = timezone.now()
                rejection_reason = form.cleaned_data.get('rejection_reason', '')
                if rejection_reason:
                    org.rejection_reason = ''
                messages.success(request, f'Organization "{org.name}" has been approved!')
                _create_org_audit_log(
                    org, 'approved', request.user,
                    f'Organization approved by {request.user.get_full_name() or request.user.username}',
                    changes, request
                )
                # Notify org admin
                org_admin = User.objects.filter(organization=org, role='org_admin').first()
                if org_admin:
                    notify_org_admin_org_status_change(org_admin, org, 'approved')
                    send_org_status_change_email(org_admin, org, 'approved')
                # Notify org members
                notify_org_owned_users_org_status_change(org, 'approved')
                
            elif new_status == 'rejected':
                rejection_reason = form.cleaned_data.get('rejection_reason', '')
                changes['rejection_reason'] = rejection_reason
                messages.info(request, f'Organization "{org.name}" has been rejected.')
                _create_org_audit_log(
                    org, 'rejected', request.user,
                    f'Organization rejected by {request.user.get_full_name() or request.user.username}. Reason: {rejection_reason}',
                    changes, request
                )
                # Notify org admin
                org_admin = User.objects.filter(organization=org, role='org_admin').first()
                if org_admin:
                    notify_org_admin_org_status_change(org_admin, org, 'rejected', old_status, rejection_reason)
                    send_org_status_change_email(org_admin, org, 'rejected', rejection_reason)
                
            elif new_status == 'suspended':
                messages.warning(request, f'Organization "{org.name}" has been suspended.')
                _create_org_audit_log(
                    org, 'suspended', request.user,
                    f'Organization suspended by {request.user.get_full_name() or request.user.username}',
                    changes, request
                )
                # Notify org admin
                org_admin = User.objects.filter(organization=org, role='org_admin').first()
                if org_admin:
                    notify_org_admin_org_status_change(org_admin, org, 'suspended', old_status)
                    send_org_status_change_email(org_admin, org, 'suspended')
                # Notify org members
                notify_org_owned_users_org_status_change(org, 'suspended')
                
            elif new_status == 'pending':
                if old_status in ('rejected', 'suspended'):
                    messages.info(request, f'Organization "{org.name}" has been reset to pending for re-review.')
                    _create_org_audit_log(
                        org, 'status_changed', request.user,
                        f'Organization status reset to pending by {request.user.get_full_name() or request.user.username}',
                        changes, request
                    )
            
            org.save()
            return redirect('super_admin_organization_list')
    else:
        form = OrganizationApprovalForm(instance=organization)
    
    # Get recent audit logs for this org
    audit_logs = OrganizationAuditLog.objects.filter(organization=organization)[:10]
    
    return render(request, 'admin/organizations/organization_approve.html', {
        'form': form,
        'organization': organization,
        'old_status': old_status,
        'audit_logs': audit_logs,
    })


@login_required
@super_admin_required
def super_admin_toggle_org_status(request, pk):
    """Quick toggle to activate/deactivate an organization with audit logging."""
    organization = get_object_or_404(Organization, pk=pk)
    
    if request.method == 'POST':
        was_active = organization.is_active
        organization.is_active = not was_active
        organization.save()
        
        status = "activated" if organization.is_active else "deactivated"
        _create_org_audit_log(
            organization, 'updated', request.user,
            f'Organization {status} by {request.user.get_full_name() or request.user.username}',
            {'old_status': 'active' if was_active else 'inactive', 'new_status': status},
            request
        )
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
            
            # Send org admin created email if an admin was assigned
            if org_admin_user:
                temp_password = str(uuid.uuid4())[:12]
                org_admin_user.set_password(temp_password)
                org_admin_user.save()
                send_org_admin_created_email(org_admin_user, org, temp_password)
            
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
def super_admin_verify_organization(request, pk):
    """Toggle verification status for an organization."""
    organization = get_object_or_404(Organization, pk=pk)
    
    if request.method == 'POST':
        form = OrganizationVerificationForm(request.POST, instance=organization)
        if form.is_valid():
            was_verified = organization.is_verified
            org = form.save(commit=False)
            if org.is_verified and not was_verified:
                org.verified_by = request.user
                org.verified_at = timezone.now()
                action = 'verified'
                detail = f'Organization verified by {request.user.get_full_name() or request.user.username}'
                msg = f'Organization "{org.name}" has been verified!'
            elif not org.is_verified and was_verified:
                org.verified_by = None
                org.verified_at = None
                action = 'unverified'
                detail = f'Organization verification removed by {request.user.get_full_name() or request.user.username}'
                msg = f'Organization "{org.name}" verification has been removed.'
            else:
                messages.info(request, 'No changes made to verification status.')
                return redirect('super_admin_organization_detail', pk=pk)
            
            org.save()
            _create_org_audit_log(organization, action, request.user, detail, {'is_verified': org.is_verified}, request)
            messages.success(request, msg)
            
            # Notify org admin
            org_admin = User.objects.filter(organization=org, role='org_admin').first()
            if org_admin and org.is_verified:
                notify_org_admin_org_verified(org_admin, org)
                send_org_status_change_email(org_admin, org, 'verified')
            
            return redirect('super_admin_organization_detail', pk=pk)
    else:
        form = OrganizationVerificationForm(instance=organization)
    
    return render(request, 'admin/organizations/organization_verify.html', {
        'form': form,
        'organization': organization,
    })


@login_required
@super_admin_required
def super_admin_organization_delete(request, pk):
    """Delete an organization with validation for active reservations/tournaments"""

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
        _create_org_audit_log(
            organization, 'deleted', request.user,
            f'Organization "{org_name}" permanently deleted by {request.user.get_full_name() or request.user.username}',
            None, request
        )
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
def super_admin_organization_activity_log(request):
    """View all organization-related audit activity across the platform."""
    pk = request.GET.get('org_id')
    logs = OrganizationAuditLog.objects.select_related('organization', 'performed_by').all().order_by('-created_at')
    
    if pk:
        try:
            organization = get_object_or_404(Organization, pk=pk)
            logs = logs.filter(organization=organization)
        except (ValueError, Http404):
            pass
    
    # Filter by action
    action_filter = request.GET.get('action', '')
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    # Filter by date
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        logs = logs.filter(created_at__date__gte=date_from)
    if date_to:
        logs = logs.filter(created_at__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(logs, 30)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin/organizations/activity_log.html', {
        'logs': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'action_filter': action_filter,
        'date_from': date_from,
        'date_to': date_to,
        'total_count': OrganizationAuditLog.objects.count(),
        'org_filter': pk,
    })


@login_required
@super_admin_required
def super_admin_dashboard(request):
    """Super Admin main dashboard with system-wide analytics"""
    
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
    fourteen_days_ago = today - timedelta(days=13)
    daily_revenues = Payment.objects.filter(
        status='paid',
        created_at__date__gte=fourteen_days_ago    ).extra(
        select={'day': 'DATE(payments.created_at)'}
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
def org_admin_analytics_view(request):
    """Org Admin analytics dashboard with org-scoped charts and metrics"""

    organization = request.user.organization
    today = timezone.now().date()

    # Org-scoped queries
    org_courts = Court.objects.filter(organization=organization, is_active=True)
    org_reservations = Reservation.objects.filter(court__organization=organization)
    org_payments = Payment.objects.filter(reservation__court__organization=organization)

    # Key metrics
    total_courts = org_courts.count()
    total_reservations = org_reservations.exclude(status='cancelled').count()
    pending_reservations = org_reservations.filter(status='pending').count()
    confirmed_reservations = org_reservations.filter(status='confirmed').count()
    today_reservations = org_reservations.filter(date=today).count()

    # Revenue stats
    revenue_stats = {
        'total_revenue': org_payments.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0,
        'today_revenue': org_payments.filter(status='paid', created_at__date=today).aggregate(Sum('amount'))['amount__sum'] or 0,
        'month_revenue': org_payments.filter(status='paid', created_at__year=today.year, created_at__month=today.month).aggregate(Sum('amount'))['amount__sum'] or 0,
        'pending_amount': org_payments.filter(status='pending').aggregate(Sum('amount'))['amount__sum'] or 0,
    }

    # Revenue trend (last 14 days)
    fourteen_days_ago = today - timedelta(days=13)
    daily_revenues = org_payments.filter(
        status='paid',
        created_at__date__gte=fourteen_days_ago
    ).extra(
        select={'day': 'DATE(payments.created_at)'}
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

    # Court usage
    court_usage = org_reservations.filter(
        status__in=['confirmed', 'completed']
    ).values('court__name').annotate(
        total=Count('id')
    ).order_by('-total')[:10]

    # Peak hours (last 30 days)
    thirty_days_ago = today - timedelta(days=30)
    hourly_bookings = org_reservations.filter(
        created_at__date__gte=thirty_days_ago,
        status__in=['confirmed', 'completed', 'pending']
    ).annotate(
        hour=ExtractHour('start_time')
    ).values('hour').annotate(
        count=Count('id'),
        revenue=Sum('total_amount')
    ).order_by('hour')

    peak_hours_labels = []
    peak_hours_counts = []
    peak_hours_revenue = []
    for h in range(8, 23):
        peak_hours_labels.append(f"{h}:00")
        found = next((item for item in hourly_bookings if item['hour'] == h), None)
        peak_hours_counts.append(found['count'] if found else 0)
        peak_hours_revenue.append(float(found['revenue'] or 0) if found else 0)

    # Revenue by payment method
    revenue_by_method = list(org_payments.filter(status='paid').values('method').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total'))

    # Revenue comparison
    this_month_revenue = org_payments.filter(
        status='paid', created_at__year=today.year, created_at__month=today.month
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    last_month = today.month - 1 if today.month > 1 else 12
    last_month_year = today.year if today.month > 1 else today.year - 1
    last_month_revenue = org_payments.filter(
        status='paid', created_at__year=last_month_year, created_at__month=last_month
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    revenue_growth = round(
        ((this_month_revenue - last_month_revenue) / last_month_revenue * 100) if last_month_revenue > 0 else 0, 1
    )

    # Recent reservations
    recent_reservations = org_reservations.select_related('user', 'court').order_by('-created_at')[:10]

    # Refunds
    total_refunds = Refund.objects.filter(
        status='processed', payment__reservation__court__organization=organization
    ).aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'admin/organizations/org_admin_analytics.html', {
        'organization': organization,
        'total_courts': total_courts,
        'total_reservations': total_reservations,
        'pending_reservations': pending_reservations,
        'confirmed_reservations': confirmed_reservations,
        'today_reservations': today_reservations,
        'revenue_stats': revenue_stats,
        'revenue_trend_labels': revenue_trend_labels,
        'revenue_trend_values': revenue_trend_values,
        'booking_trend_values': booking_trend_values,
        'court_usage': court_usage,
        'revenue_by_method': revenue_by_method,
        'peak_hours_labels': peak_hours_labels,
        'peak_hours_counts': peak_hours_counts,
        'peak_hours_revenue': peak_hours_revenue,
        'this_month_revenue': this_month_revenue,
        'last_month_revenue': last_month_revenue,
        'revenue_growth': revenue_growth,
        'recent_reservations': recent_reservations,
        'total_refunds': total_refunds,
    })


@login_required
@org_admin_required
@org_required
def org_admin_manage_staff(request):
    """Organization Admin manages staff members for their organization."""
    org = request.user.organization

    # Get all staff members
    staff_members = User.objects.filter(
        organization=org,
        role='org_staff'
    ).order_by('username')

    # Handle POST actions
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_max':
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

    # Search and filtering
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    department_filter = request.GET.get('department', '')

    filtered_staff = staff_members
    if search_query:
        filtered_staff = filtered_staff.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(staff_id__icontains=search_query) |
            Q(username__icontains=search_query)
        )
    if status_filter == 'active':
        filtered_staff = filtered_staff.filter(is_active=True, employment_status='active')
    elif status_filter == 'inactive':
        filtered_staff = filtered_staff.filter(Q(is_active=False) | Q(employment_status='inactive'))
    elif status_filter == 'suspended':
        filtered_staff = filtered_staff.filter(employment_status='suspended')
    if department_filter:
        filtered_staff = filtered_staff.filter(department__iexact=department_filter)

    # Sorting
    sort_by = request.GET.get('sort_by', '-created_at')
    sort_order = request.GET.get('sort_order', 'desc')
    allowed_sort_fields = ['username', 'first_name', 'last_name', 'email', 'staff_id', 'department', 'is_active', 'created_at', 'last_login']
    if sort_by.lstrip('-') in allowed_sort_fields:
        if sort_order == 'asc' and sort_by.startswith('-'):
            sort_by = sort_by[1:]
        elif sort_order == 'desc' and not sort_by.startswith('-'):
            sort_by = '-' + sort_by
        filtered_staff = filtered_staff.order_by(sort_by)

    # Pagination
    paginator = Paginator(filtered_staff, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Stats
    total_staff = staff_members.count()
    active_staff = staff_members.filter(is_active=True, employment_status='active').count()
    inactive_staff = staff_members.filter(Q(is_active=False) | Q(employment_status='inactive')).count()
    recently_added = staff_members.filter(created_at__gte=timezone.now() - timedelta(days=30)).count()

    # Departments list for filter
    departments = staff_members.exclude(department__isnull=True).exclude(department='').values_list('department', flat=True).distinct().order_by('department')

    can_add = org.can_add_staff()
    staff_limit = org.max_staff_accounts

    return render(request, 'admin/organizations/org_admin_staff.html', {
        'organization': org,
        'staff_members': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'search_query': search_query,
        'status_filter': status_filter,
        'department_filter': department_filter,
        'sort_by': sort_by,
        'sort_order': sort_order,
        'total_staff': total_staff,
        'active_staff': active_staff,
        'inactive_staff': inactive_staff,
        'recently_added': recently_added,
        'departments': departments,
        'can_add': can_add,
        'staff_limit': staff_limit,
        'current_staff_count': total_staff,
    })


@login_required
@org_admin_required
@org_required
def org_admin_staff_export_csv(request):
    """Export staff list as CSV."""
    org = request.user.organization
    staff_members = User.objects.filter(
        organization=org,
        role='org_staff'
    ).order_by('username')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{org.name}_staff_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Staff ID', 'First Name', 'Middle Name', 'Last Name', 'Email', 'Phone', 'Department', 'Status', 'Employment Status', 'Last Login', 'Created At'])
    
    for staff in staff_members:
        writer.writerow([
            staff.staff_id or '',
            staff.first_name,
            staff.middle_name or '',
            staff.last_name,
            staff.email,
            staff.phone_number or '',
            staff.department or '',
            'Active' if staff.is_active else 'Inactive',
            staff.get_employment_status_display() if staff.employment_status else '',
            staff.last_login.strftime('%Y-%m-%d %H:%M:%S') if staff.last_login else '',
            staff.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])
    
    return response


@login_required
@org_admin_required
@org_required
def org_admin_staff_create(request):
    """Create a new staff account within the organization.
    Renders inline on validation errors instead of redirecting with messages."""
    org = request.user.organization

    if not org.can_add_staff():
        messages.error(request, 'Staff limit reached. Increase the limit or remove an existing staff member.')
        return redirect('org_admin_manage_staff')

    form = StaffAccountCreateForm(org=org)

    if request.method == 'POST':
        form = StaffAccountCreateForm(request.POST, request.FILES, org=org)
        if form.is_valid():
            user = form.save()
            _create_org_audit_log(org, 'staff_added', request.user,
                f'Staff account "{user.get_full_name() or user.username}" (ID: {user.staff_id}) created by {request.user.get_full_name() or request.user.username}',
                request=request)
            UserActivity.objects.create(
                user=request.user,
                action=f'Created staff account: {user.get_full_name() or user.username} ({user.staff_id})'
            )
            # Send welcome email if SMTP configured
            try:
                from notifications.email_utils import send_staff_welcome_email
                send_staff_welcome_email(user, org, form.cleaned_data.get('password', ''))
            except Exception:
                pass  # Email sending is best-effort
            messages.success(request, f'Staff account created successfully! Staff ID: {user.staff_id}')
            return redirect('org_admin_manage_staff')

    # Re-render the staff management page with the form errors shown inline
    staff_members = User.objects.filter(organization=org, role='org_staff').order_by('username')
    total_staff = staff_members.count()
    active_staff = staff_members.filter(is_active=True, employment_status='active').count()
    inactive_staff = staff_members.filter(Q(is_active=False) | Q(employment_status='inactive')).count()
    recently_added = staff_members.filter(created_at__gte=timezone.now() - timedelta(days=30)).count()
    departments = staff_members.exclude(department__isnull=True).exclude(department='').values_list('department', flat=True).distinct().order_by('department')
    can_add = org.can_add_staff()
    staff_limit = org.max_staff_accounts

    # Build form_data dict from submitted POST data for inline form display
    form_data = {
        'first_name': request.POST.get('first_name', ''),
        'middle_name': request.POST.get('middle_name', ''),
        'last_name': request.POST.get('last_name', ''),
        'email': request.POST.get('email', ''),
        'username': request.POST.get('username', ''),
        'phone_number': request.POST.get('phone_number', ''),
        'gender': request.POST.get('gender', ''),
        'birth_date': request.POST.get('birth_date', ''),
        'department': request.POST.get('department', ''),
        'employment_status': request.POST.get('employment_status', 'active'),
        'notes': request.POST.get('notes', ''),
    }

    # Create a simple paginator for template compatibility
    paginator = Paginator(staff_members, 10)
    page_obj = paginator.get_page(1)
    sort_by = '-created_at'
    sort_order = 'desc'

    return render(request, 'admin/organizations/org_admin_staff.html', {
        'organization': org,
        'staff_members': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'search_query': '',
        'status_filter': '',
        'department_filter': '',
        'sort_by': sort_by,
        'sort_order': sort_order,
        'total_staff': total_staff,
        'active_staff': active_staff,
        'inactive_staff': inactive_staff,
        'recently_added': recently_added,
        'departments': departments,
        'can_add': can_add,
        'staff_limit': staff_limit,
        'current_staff_count': total_staff,
        'form_data': form_data,
        'form_open': True,  # Flag to auto-open the create modal
    })


@login_required
@org_admin_required
@org_required
def org_admin_staff_detail(request, staff_id):
    """View a staff member's full profile."""
    org = request.user.organization
    staff = get_object_or_404(User, id=staff_id, organization=org, role='org_staff')

    # Get recent activity
    recent_activities = UserActivity.objects.filter(user=staff).order_by('-created_at')[:20]

    # Get permissions
    permissions = StaffPermission.objects.filter(user=staff).first()

    return render(request, 'admin/organizations/org_admin_staff_detail.html', {
        'organization': org,
        'staff': staff,
        'recent_activities': recent_activities,
        'permissions': permissions,
    })


@login_required
@org_admin_required
@org_required
def org_admin_staff_edit(request, staff_id):
    """Edit a staff member's details."""
    org = request.user.organization
    staff = get_object_or_404(User, id=staff_id, organization=org, role='org_staff')

    if request.method == 'POST':
        form = StaffEditForm(request.POST, request.FILES, instance=staff)
        if form.is_valid():
            form.save()
            _create_org_audit_log(org, 'updated', request.user,
                f'Staff "{staff.get_full_name() or staff.username}" updated by {request.user.get_full_name() or request.user.username}',
                request=request)
            messages.success(request, 'Staff account updated successfully.')
            return redirect('org_admin_staff_detail', staff_id=staff.id)
    else:
        form = StaffEditForm(instance=staff)

    return render(request, 'admin/organizations/org_admin_staff_detail.html', {
        'organization': org,
        'staff': staff,
        'form': form,
        'edit_mode': True,
        'permissions': StaffPermission.objects.filter(user=staff).first(),
    })


@login_required
@org_admin_required
@org_required
def org_admin_staff_permissions(request, staff_id):
    """Manage staff permissions."""
    org = request.user.organization
    staff = get_object_or_404(User, id=staff_id, organization=org, role='org_staff')

    permissions, created = StaffPermission.objects.get_or_create(
        user=staff
    )

    if request.method == 'POST':
        form = StaffPermissionForm(request.POST, instance=permissions)
        if form.is_valid():
            form.save()
            _create_org_audit_log(org, 'settings_changed', request.user,
                f'Permissions updated for staff "{staff.get_full_name() or staff.username}" by {request.user.get_full_name() or request.user.username}',
                request=request)
            messages.success(request, 'Staff permissions updated successfully.')
            return redirect('org_admin_staff_detail', staff_id=staff.id)
    else:
        form = StaffPermissionForm(instance=permissions)

    return render(request, 'admin/organizations/org_admin_staff_permissions.html', {
        'organization': org,
        'staff': staff,
        'form': form,
    })


@login_required
@org_admin_required
@org_required
def org_admin_staff_toggle_status(request, staff_id):
    """Activate or deactivate a staff account."""
    org = request.user.organization
    staff = get_object_or_404(User, id=staff_id, organization=org, role='org_staff')

    if request.method == 'POST':
        action = request.POST.get('status_action', 'toggle')
        if action == 'activate':
            staff.is_active = True
            staff.employment_status = 'active'
            msg = 'activated'
        elif action == 'deactivate':
            staff.is_active = False
            staff.employment_status = 'inactive'
            msg = 'deactivated'
        elif action == 'suspend':
            staff.is_active = False
            staff.employment_status = 'suspended'
            msg = 'suspended'
        else:
            staff.is_active = not staff.is_active
            staff.employment_status = 'active' if staff.is_active else 'inactive'
            msg = 'activated' if staff.is_active else 'deactivated'

        staff.save(update_fields=['is_active', 'employment_status'])
        _create_org_audit_log(org, 'updated', request.user,
            f'Staff "{staff.get_full_name() or staff.username}" {msg} by {request.user.get_full_name() or request.user.username}',
            request=request)
        messages.success(request, f'Staff account {msg} successfully.')

    return redirect('org_admin_manage_staff')


@login_required
@org_admin_required
@org_required
def org_admin_staff_reset_password(request, staff_id):
    """Reset a staff member's password and show it on a dedicated page."""
    org = request.user.organization
    staff = get_object_or_404(User, id=staff_id, organization=org, role='org_staff')

    if request.method == 'POST':
        import uuid as uuid_lib
        new_password = str(uuid_lib.uuid4())[:12]
        staff.set_password(new_password)
        staff.save(update_fields=['password'])
        _create_org_audit_log(org, 'updated', request.user,
            f'Password reset for staff "{staff.get_full_name() or staff.username}" by {request.user.get_full_name() or request.user.username}',
            request=request)
        # Render the password reset confirmation page securely (not in flash message)
        response = TemplateResponse(request, 'admin/organizations/org_admin_staff_password_reset.html', {
            'organization': org,
            'staff': staff,
            'new_password': new_password,
        })
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    messages.info(request, 'Click "Reset Password" again to confirm.')
    return redirect('org_admin_staff_detail', staff_id=staff.id)


@login_required
@org_admin_required
@org_required
def org_admin_staff_send_reset_email(request, staff_id):
    """Send a password reset email to a staff member."""
    from django.conf import settings

    org = request.user.organization
    staff = get_object_or_404(User, id=staff_id, organization=org, role='org_staff')

    if request.method == 'POST':
        try:
            # Generate password reset token
            uidb64 = urlsafe_base64_encode(force_bytes(staff.pk))
            token = default_token_generator.make_token(staff)
            reset_url = f'{settings.SITE_URL}/reset/{uidb64}/{token}/'
            
            # Send the email
            send_password_reset_email(staff, reset_url)
            
            _create_org_audit_log(org, 'updated', request.user,
                f'Password reset email sent to staff "{staff.get_full_name() or staff.username}" by {request.user.get_full_name() or request.user.username}',
                request=request)
            UserActivity.objects.create(
                user=request.user,
                action='Sent password reset email',
                details=f'Password reset email sent to {staff.email}'
            )
            messages.success(request, f'Password reset email sent to {staff.email}.')
        except Exception as e:
            messages.error(request, f'Failed to send password reset email: {str(e)}')
        
        return redirect('org_admin_staff_detail', staff_id=staff.id)

    return redirect('org_admin_staff_detail', staff_id=staff.id)


@login_required
@org_admin_required
@org_required
def org_admin_staff_delete(request, staff_id):
    """Delete a staff account (demote to regular user)."""
    org = request.user.organization
    staff = get_object_or_404(User, id=staff_id, organization=org, role='org_staff')

    if request.method == 'POST':
        staff_name = staff.get_full_name() or staff.username
        # Remove organization and demote to user
        staff.organization = None
        staff.role = 'user'
        staff.is_active = False
        staff.staff_id = None
        staff.sync_employment_status()
        staff.save(update_fields=['organization', 'role', 'is_active', 'staff_id', 'employment_status'])
        # Remove permissions
        StaffPermission.objects.filter(user=staff).delete()
        _create_org_audit_log(org, 'staff_removed', request.user,
            f'Staff "{staff_name}" deleted/demoted by {request.user.get_full_name() or request.user.username}',
            request=request)
        messages.success(request, f'Staff account "{staff_name}" has been removed.')

    return redirect('org_admin_manage_staff')


@login_required
@org_admin_required
@org_required
def org_admin_org_activity_log(request):
    """Org Admin view of their own organization's audit activity."""
    org = request.user.organization
    logs = OrganizationAuditLog.objects.filter(organization=org).select_related('performed_by').order_by('-created_at')
    
    # Filter by action
    action_filter = request.GET.get('action', '')
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    # Filter by date
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        logs = logs.filter(created_at__date__gte=date_from)
    if date_to:
        logs = logs.filter(created_at__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(logs, 30)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin/organizations/activity_log.html', {
        'logs': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'action_filter': action_filter,
        'date_from': date_from,
        'date_to': date_to,
        'organization': org,
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
