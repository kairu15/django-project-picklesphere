"""
Maintenance Mode Middleware

Blocks all requests from non-super-admin users when maintenance mode is active.
Super admins can still log in and access the system to perform maintenance.
Also auto-disables maintenance if scheduled_end has passed.
"""

from django.shortcuts import render
from django.utils import timezone
from django.urls import resolve, Resolver404


class MaintenanceModeMiddleware:
    """Middleware that checks maintenance mode and blocks non-admin users."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip maintenance check for static/media files and admin page
        path = request.path_info
        if path.startswith('/static/') or path.startswith('/media/'):
            return self.get_response(request)

        # Check if maintenance mode is active
        from .models import MaintenanceMode

        try:
            maintenance = MaintenanceMode.objects.get(pk=1)
        except MaintenanceMode.DoesNotExist:
            return self.get_response(request)

        # Auto-disable if scheduled end has passed
        if maintenance.is_active and maintenance.scheduled_end:
            if timezone.now() >= maintenance.scheduled_end:
                maintenance.is_active = False
                maintenance.last_disabled_at = timezone.now()
                maintenance.save(update_fields=['is_active', 'last_disabled_at'])

                # Log auto-disable
                from .models import MaintenanceAuditLog
                MaintenanceAuditLog.objects.create(
                    action='auto_disabled',
                    details='Auto-disabled because scheduled end time was reached.',
                    ip_address=request.META.get('REMOTE_ADDR'),
                )
                return self.get_response(request)

        # If maintenance is NOT active, proceed normally
        if not maintenance.is_active:
            return self.get_response(request)

        # If maintenance IS active, allow super admins through
        if request.user.is_authenticated and request.user.is_super_admin():
            return self.get_response(request)

        # Also allow login page so super admins can log in
        if path.startswith('/accounts/login/') or path.startswith('/accounts/logout/'):
            return self.get_response(request)

        # Show maintenance page for everyone else
        return render(request, 'maintenance.html', {
            'maintenance': maintenance,
            'page_title': 'System Under Maintenance',
        })
