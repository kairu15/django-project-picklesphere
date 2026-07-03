from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
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
            if user.is_admin():
                return redirect('admin_dashboard')
            elif user.is_staff_user():
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
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'auth/profile.html', {'form': form})


@login_required
@admin_required
def user_list_view(request):
    
    users = User.objects.all().order_by('-created_at')
    
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
    
    return render(request, 'admin/users/user_list.html', {
        'users': users,
        'search_query': search_query,
        'role_filter': role_filter
    })


@login_required
@admin_required
def user_edit_view(request, user_id):
    
    user = get_object_or_404(User, id=user_id)
    
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
            created_user = form.save()
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
    
    user_to_delete = get_object_or_404(User, id=user_id)
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
    return render(request, 'admin/activity_log.html', {'activities': activities})
