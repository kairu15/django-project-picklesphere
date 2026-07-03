from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.conf import settings


def admin_required(view_func):
    """
    Decorator that restricts access to admin users only.
    Must be used after (below) @login_required.
    Redirects non-admin users to their dashboard with an error message.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin():
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def staff_or_admin_required(view_func):
    """
    Decorator that restricts access to staff or admin users only.
    Must be used after (below) @login_required.
    Redirects regular users to their dashboard with an error message.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or (not request.user.is_staff_user() and not request.user.is_admin()):
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def user_required(view_func):
    """
    Decorator that restricts access to regular users only.
    Must be used after (below) @login_required.
    Redirects staff and admin users to their respective dashboards with an error message.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_normal_user():
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
