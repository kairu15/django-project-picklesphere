from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .forms import (
    UserRegistrationForm,
    UserLoginForm,
    UserProfileForm,
    UserRoleForm,
    AdminUserCreateForm,
    AdminUserUpdateForm,
)
from .models import User, UserActivity
from .decorators import admin_required, staff_or_admin_required, user_required
from notifications.models import Notification


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'user'
            user.save()
            
            # Create welcome notification
            Notification.objects.create(
                user=user,
                message=f"Welcome to PickleSphere, {user.first_name}! Your account has been created successfully."
            )
            
            messages.success(request, 'Account created successfully! Please sign in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Log activity
            UserActivity.objects.create(
                user=user,
                action='Login',
                details=f'User logged in from {request.META.get("REMOTE_ADDR")}'
            )
            
            messages.success(request, f'Welcome back, {user.first_name}!')
            
            # Redirect based on role
            if user.is_super_admin():
                return redirect('super_admin_dashboard')
            elif user.is_org_admin():
                return redirect('org_admin_dashboard')
            elif user.is_org_staff():
                return redirect('staff_dashboard')
            else:
                return redirect('user_dashboard')
    else:
        form = UserLoginForm()
    
    return render(request, 'auth/login.html', {'form': form})


@login_required
def logout_view(request):
    # Log activity
    UserActivity.objects.create(
        user=request.user,
        action='Logout',
        details=f'User logged out from {request.META.get("REMOTE_ADDR")}'
    )
    
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def profile_view(request):
    profile_form = UserProfileForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)
    
    # Get reservation history
    from reservations.models import Reservation
    reservation_history = Reservation.objects.filter(
        user=request.user
    ).select_related('court', 'court__site').order_by('-date', '-start_time')[:10]
    
    # Get tournament participation
    from tournaments.models import Registration
    tournament_registrations = Registration.objects.filter(
        user=request.user
    ).select_related('tournament').order_by('-registered_at')[:10]
    
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile_form = UserProfileForm(request.POST, request.FILES, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('profile')
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully!')
                return redirect('profile')
            else:
                messages.error(request, 'Please correct the password errors below.')
    
    return render(request, 'auth/profile.html', {
        'form': profile_form,
        'password_form': password_form,
        'reservation_history': reservation_history,
        'tournament_registrations': tournament_registrations,
    })


@login_required
@admin_required
def user_list_view(request):
    
    users = User.objects.all().order_by('-created_at')
    
    # Org-scoping for org_admin - only show users from their organization
    if request.user.is_org_admin() and request.user.organization:
        users = users.filter(organization=request.user.organization)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Filter by role
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Sorting
    sort_by = request.GET.get('sort_by', '-created_at')
    sort_order = request.GET.get('sort_order', 'desc')
    allowed_sort_fields = ['username', 'email', 'role', 'is_active', 'created_at', 'first_name', 'last_name']
    if sort_by.lstrip('-') in allowed_sort_fields:
        if sort_order == 'asc' and sort_by.startswith('-'):
            sort_by = sort_by[1:]
        elif sort_order == 'desc' and not sort_by.startswith('-'):
            sort_by = '-' + sort_by
        users = users.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin/users/user_list.html', {
        'users': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'search_query': search_query,
        'role_filter': role_filter,
        'sort_by': sort_by,
        'sort_order': sort_order,
    })


@login_required
@admin_required
def user_edit_view(request, user_id):
    
    user_qs = User.objects.all()
    # Org-scoping for org_admin
    if request.user.is_org_admin() and request.user.organization:
        user_qs = user_qs.filter(organization=request.user.organization)
    user = get_object_or_404(user_qs, id=user_id)
    
    if request.method == 'POST':
        form = AdminUserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User {user.username} updated successfully!')
            return redirect('user_list')
    else:
        form = AdminUserUpdateForm(instance=user)
    
    return render(request, 'admin/users/user_form.html', {
        'form': form,
        'edit_user': user
    })


@login_required
@admin_required
def user_create_view(request):
    
    if request.method == 'POST':
        form = AdminUserCreateForm(request.POST)
        if form.is_valid():
            created_user = form.save(commit=False)
            # Auto-assign organization for org_admin
            if request.user.is_org_admin() and request.user.organization:
                created_user.organization = request.user.organization
            created_user.save()
            messages.success(request, f'User {created_user.username} created successfully!')
            return redirect('user_list')
    else:
        form = AdminUserCreateForm()
    
    return render(request, 'admin/users/user_form.html', {'form': form})


@login_required
@admin_required
def user_delete_view(request, user_id):
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('user_list')
    
    user_qs = User.objects.all()
    # Org-scoping for org_admin
    if request.user.is_org_admin() and request.user.organization:
        user_qs = user_qs.filter(organization=request.user.organization)
    user_to_delete = get_object_or_404(user_qs, id=user_id)
    if user_to_delete == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('user_list')
    
    if not user_to_delete.is_active:
        messages.info(request, f'User {user_to_delete.username} is already inactive.')
        return redirect('user_list')
    
    user_to_delete.is_active = False
    user_to_delete.save(update_fields=['is_active'])
    
    messages.success(request, f'User {user_to_delete.username} deactivated successfully.')
    return redirect('user_list')


@login_required
@staff_or_admin_required
def user_activity_log(request):
    
    activities = UserActivity.objects.all().order_by('-created_at')[:100]
    # Org-scoping for org_admin - only show activities from their organization's users
    if request.user.is_org_admin() and request.user.organization:
        activities = activities.filter(user__organization=request.user.organization)
    return render(request, 'admin/activity_log.html', {'activities': activities})
