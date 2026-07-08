"""
URL configuration for PickleSphere - Role-Based Routing

Each role has its own URL prefix:
- / (public) - Home, about, contact, pricing, faq, etc.
- /super-admin/ - Super Admin system management
- /org-admin/ - Organization Admin management
- /staff/ - Organization Staff operations
- /user/ - Regular user features
- /accounts/ - Authentication
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import session_views

urlpatterns = [
    # Django Admin (superuser only)
    path('admin/', admin.site.urls),

    # ========== PUBLIC ROUTES ==========
    path('', include('dashboard.urls')),
    path('courts/', include('courts.urls')),
    path('reservations/', include('reservations.urls')),
    path('organizations/', include('organizations.urls')),
    path('tournaments/', include('tournaments.urls')),
    path('equipment/', include('equipment.urls')),
    path('accounts/', include('accounts.urls')),

    # ========== SUPER ADMIN ROUTES (/super-admin/) ==========
    path('super-admin/', include('dashboard.admin_urls')),
    path('super-admin/', include('accounts.admin_urls')),
    path('super-admin/', include('organizations.admin_urls')),
    path('super-admin/', include('reservations.admin_urls')),
    path('super-admin/', include('payments.admin_urls')),
    path('super-admin/', include('equipment.admin_urls')),
    path('super-admin/', include('tournaments.admin_urls')),
    path('super-admin/', include('notifications.admin_urls')),

    # ========== ORGANIZATION ADMIN ROUTES (/org-admin/) ==========
    path('org-admin/', include('organizations.org_urls')),
    path('org-admin/', include('accounts.org_urls')),
    path('org-admin/', include('courts.org_urls')),
    path('org-admin/', include('reservations.org_urls')),
    path('org-admin/', include('payments.org_urls')),
    path('org-admin/', include('equipment.staff_urls')),
    path('org-admin/', include('tournaments.admin_urls')),
    path('org-admin/', include('notifications.org_urls')),

    # ========== STAFF ROUTES (/staff/) ==========
    path('staff/', include('dashboard.staff_urls')),
    path('staff/', include('reservations.staff_urls')),
    path('staff/', include('payments.staff_urls')),
    path('staff/', include('equipment.staff_urls')),
    path('staff/', include('notifications.staff_urls')),

    # ========== USER ROUTES (/user/) ==========
    path('user/', include('dashboard.user_urls')),
    path('user/', include('reservations.user_urls')),
    path('user/', include('payments.user_urls')),
    path('user/', include('equipment.user_urls')),
    path('user/', include('tournaments.user_urls')),
    path('user/', include('notifications.user_urls')),

    # ========== SHARED / NOTIFICATIONS ==========
    # Shared notification routes handled via notifications.urls
    path('notifications/', include('notifications.urls')),

    # ========== SCORING ==========
    path('scoring/', include('scoring.urls')),

    # ========== SESSION MANAGEMENT API ==========
    path('api/session/heartbeat/', session_views.session_heartbeat, name='session_heartbeat'),
    path('api/session/info/', session_views.session_info, name='session_info'),
    path('api/session/extend/', session_views.extend_session, name='extend_session'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'static')
