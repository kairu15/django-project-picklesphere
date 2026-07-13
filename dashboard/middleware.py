"""
Maintenance Mode Middleware

Blocks all requests from non-super-admin users when maintenance mode is active.
Super admins can still log in and access the system to perform maintenance.
Also auto-disables maintenance if scheduled_end has passed.

Uses caching to avoid a database hit on every request — the common case
(maintenance is OFF) is served entirely from cache with zero DB queries.
"""

from django.shortcuts import render
from django.utils import timezone
from django.core.cache import cache


class MaintenanceModeMiddleware:
    """Middleware that checks maintenance mode and blocks non-admin users.
    Uses caching to avoid a database hit on every request."""

    CACHE_KEY = 'maintenance_mode_data'
    CACHE_TIMEOUT = 30  # seconds — short enough to pick up changes quickly

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip maintenance check for static/media files and admin page
        path = request.path_info
        if path.startswith('/static/') or path.startswith('/media/'):
            return self.get_response(request)

        # Check cache first to avoid DB hit on every request
        data = cache.get(self.CACHE_KEY)

        if data is None:
            # Cache miss — query the database
            from .models import MaintenanceMode
            try:
                maint = MaintenanceMode.objects.get(pk=1)
                data = {
                    'is_active': maint.is_active,
                    'scheduled_end': maint.scheduled_end.isoformat() if maint.scheduled_end else None,
                    'title': maint.title,
                    'message': maint.message,
                    'banner_image_url': maint.banner_image.url if maint.banner_image else None,
                    'estimated_return': maint.estimated_return.isoformat() if maint.estimated_return else None,
                    'show_contact_info': maint.show_contact_info,
                    'contact_email': maint.contact_email,
                    'contact_phone': maint.contact_phone,
                    'scheduled_start': maint.scheduled_start.isoformat() if maint.scheduled_start else None,
                }
            except MaintenanceMode.DoesNotExist:
                data = {'is_active': False}
            # Cache the result so subsequent requests skip the DB
            cache.set(self.CACHE_KEY, data, self.CACHE_TIMEOUT)

        # Auto-disable if scheduled end has passed (need DB for this write)
        if data.get('is_active') and data.get('scheduled_end'):
            scheduled_end = timezone.datetime.fromisoformat(data['scheduled_end'])
            if scheduled_end.tzinfo is None:
                scheduled_end = timezone.make_aware(scheduled_end)
            if timezone.now() >= scheduled_end:
                # Need DB access for the write — this is rare
                from .models import MaintenanceMode
                try:
                    maint = MaintenanceMode.objects.get(pk=1)
                    maint.is_active = False
                    maint.last_disabled_at = timezone.now()
                    maint.save(update_fields=['is_active', 'last_disabled_at'])
                    # Invalidate cache
                    cache.delete(self.CACHE_KEY)

                    from .models import MaintenanceAuditLog
                    MaintenanceAuditLog.objects.create(
                        action='auto_disabled',
                        details='Auto-disabled because scheduled end time was reached.',
                        ip_address=request.META.get('REMOTE_ADDR'),
                    )
                except MaintenanceMode.DoesNotExist:
                    pass
                return self.get_response(request)

        # If maintenance is NOT active, proceed normally
        if not data.get('is_active'):
            return self.get_response(request)

        # If maintenance IS active, allow super admins through
        if request.user.is_authenticated and request.user.is_super_admin():
            return self.get_response(request)

        # Also allow login page so super admins can log in
        if path.startswith('/accounts/login/') or path.startswith('/accounts/logout/'):
            return self.get_response(request)

        # Show maintenance page for everyone else
        return render(request, 'maintenance.html', {
            'maintenance': data,
            'page_title': 'System Under Maintenance',
        })
