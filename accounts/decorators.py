from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect


def super_admin_required(view_func):
    """
    Decorator that restricts access to Super Admin users only.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to continue.')
            return redirect('login')
        if not request.user.is_super_admin():
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def org_admin_required(view_func):
    """
    Decorator that restricts access to Organization Admin users (or super_admin).
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to continue.')
            return redirect('login')
        if not (request.user.is_org_admin() or request.user.is_super_admin()):
            messages.error(request, 'You do not have permission to access this page.')
            if request.user.is_super_admin():
                return redirect('super_admin_dashboard')
            return redirect('user_dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def org_staff_or_admin_required(view_func):
    """
    Decorator that restricts access to organization staff or admin (or super_admin).
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to continue.')
            return redirect('login')
        if not (request.user.is_org_staff() or request.user.is_org_admin() or request.user.is_super_admin()):
            messages.error(request, 'You do not have permission to access this page.')
            if request.user.is_super_admin():
                return redirect('super_admin_dashboard')
            return redirect('user_dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def admin_required(view_func):
    """
    Decorator that restricts access to admin-level users (super_admin or org_admin).
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to continue.')
            return redirect('login')
        if not request.user.is_admin():
            messages.error(request, 'You do not have permission to access this page.')
            if request.user.is_org_staff():
                return redirect('staff_dashboard')
            return redirect('user_dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def staff_or_admin_required(view_func):
    """
    Decorator that restricts access to staff or admin users.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to continue.')
            return redirect('login')
        if not request.user.is_staff_user():
            messages.error(request, 'You do not have permission to access this page.')
            if request.user.is_super_admin():
                return redirect('super_admin_dashboard')
            return redirect('user_dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def user_required(view_func):
    """
    Decorator that restricts access to regular users only.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to continue.')
            return redirect('login')
        if not request.user.is_normal_user():
            messages.error(request, 'You do not have permission to access this page.')
            if request.user.is_super_admin():
                return redirect('super_admin_dashboard')
            elif request.user.is_org_admin():
                return redirect('org_admin_dashboard')
            elif request.user.is_org_staff():
                return redirect('staff_dashboard')
            return redirect('user_dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def org_required(view_func):
    """
    Decorator that ensures the user belongs to an organization.
    For org_admin and org_staff users.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to continue.')
            return redirect('login')
        if not request.user.organization:
            messages.error(request, 'You are not associated with any organization.')
            if request.user.is_super_admin():
                return redirect('super_admin_dashboard')
            return redirect('user_dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
