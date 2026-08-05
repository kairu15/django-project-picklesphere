from django.core.cache import caches

from reservations.models import Reservation, CancellationRequest
from equipment.models import EquipmentRental
from payments.models import Payment
from tournaments.models import Registration
from dashboard.models import ContactMessage
from organizations.models import Organization

# Badge counts are cached per user for a short window (30s). They are quick to
# rebuild and a few seconds of staleness on a notification badge is acceptable;
# a full invalidation on every reservation/payment/registration change would
# cost more than the caching saves.
_BADGES_TTL = 30


def _compute_badges(user):
    context = {
        'badge_pending_reservations': 0,
        'badge_pending_payments': 0,
        'badge_pending_equipment': 0,
        'badge_pending_tournaments': 0,
        'badge_active_matches': 0,
        'badge_contact_messages': 0,
        'badge_my_pending_reservations': 0,
        'badge_my_pending_payments': 0,
        'badge_my_rentals': 0,
        'badge_my_tournaments': 0,
        'badge_user_messages': 0,
        'badge_pending_organizations': 0,
        'badge_pending_cancellations': 0,
        'badge_pending_refunds': 0,
    }

    # ========== SUPER ADMIN ==========
    # Super Admin sees system-wide counts
    if user.is_super_admin():
        context['badge_pending_organizations'] = Organization.objects.filter(status='pending').count()

        # Pending cancellations (awaiting staff approval)
        context['badge_pending_cancellations'] = CancellationRequest.objects.filter(
            approved__isnull=True
        ).count()

        # Pending refunds (approved cancellation, not yet refunded)
        context['badge_pending_refunds'] = CancellationRequest.objects.filter(
            approved=True,
            refund_processed=False
        ).count()

        # Pending reservations (pending status)
        context['badge_pending_reservations'] = Reservation.objects.filter(
            status='pending'
        ).count()

        # Pending payments (online payments that need verification)
        context['badge_pending_payments'] = Payment.objects.filter(
            status='pending',
            method__in=['gcash', 'maya', 'bank_transfer']
        ).count()

        # Pending equipment rentals (reserved status, pending payment)
        context['badge_pending_equipment'] = EquipmentRental.objects.filter(
            status='reserved'
        ).count()

        # Tournament registrations pending
        context['badge_pending_tournaments'] = Registration.objects.filter(
            status='pending'
        ).count()

        # Unread contact messages
        context['badge_contact_messages'] = ContactMessage.objects.filter(
            is_read=False
        ).count()

    # ========== ORG ADMIN ==========
    # Org Admin sees counts scoped to their organization
    elif user.is_org_admin() and user.organization:
        org = user.organization
        org_court_ids = org.courts.values_list('id', flat=True)

        # Pending reservations in the org's courts
        context['badge_pending_reservations'] = Reservation.objects.filter(
            court_id__in=org_court_ids,
            status='pending'
        ).count()

        # Pending cancellations in the org's courts
        context['badge_pending_cancellations'] = CancellationRequest.objects.filter(
            reservation__court_id__in=org_court_ids,
            approved__isnull=True
        ).count()

        # Pending refunds in the org's courts
        context['badge_pending_refunds'] = CancellationRequest.objects.filter(
            reservation__court_id__in=org_court_ids,
            approved=True,
            refund_processed=False
        ).count()

        # Pending payments for the org's reservations
        context['badge_pending_payments'] = Payment.objects.filter(
            reservation__court_id__in=org_court_ids,
            status='pending',
            method__in=['gcash', 'maya', 'bank_transfer']
        ).count()

        # Pending equipment rentals for the org
        context['badge_pending_equipment'] = EquipmentRental.objects.filter(
            equipment__organization=org,
            status='reserved'
        ).count()

        # Tournament registrations pending for the org's tournaments
        context['badge_pending_tournaments'] = Registration.objects.filter(
            tournament__organization=org,
            status='pending'
        ).count()

        # Unread contact messages (system-wide, not org-scoped)
        context['badge_contact_messages'] = ContactMessage.objects.filter(
            is_read=False
        ).count()

    # ========== ORG STAFF ==========
    # Org Staff sees counts scoped to their organization
    elif user.is_org_staff() and user.organization:
        org = user.organization
        org_court_ids = org.courts.values_list('id', flat=True)

        # Pending reservations for staff verification
        context['badge_pending_reservations'] = Reservation.objects.filter(
            court_id__in=org_court_ids,
            status='pending'
        ).count()

        # Pending cancellations in the org's courts
        context['badge_pending_cancellations'] = CancellationRequest.objects.filter(
            reservation__court_id__in=org_court_ids,
            approved__isnull=True
        ).count()

        # Pending refunds in the org's courts
        context['badge_pending_refunds'] = CancellationRequest.objects.filter(
            reservation__court_id__in=org_court_ids,
            approved=True,
            refund_processed=False
        ).count()

        # Payments needing verification (pending online payments)
        context['badge_pending_payments'] = Payment.objects.filter(
            reservation__court_id__in=org_court_ids,
            status='pending',
            method__in=['gcash', 'maya', 'bank_transfer']
        ).count()

        # Equipment rentals needing checkout
        context['badge_pending_equipment'] = EquipmentRental.objects.filter(
            equipment__organization=org,
            status='reserved',
            payment_status='paid'
        ).count()

    # ========== REGULAR USER ==========
    else:
        # User's pending reservations
        context['badge_my_pending_reservations'] = Reservation.objects.filter(
            user=user,
            status='pending'
        ).count()

        # User's pending payments
        context['badge_my_pending_payments'] = Payment.objects.filter(
            reservation__user=user,
            status='pending'
        ).count()

        # User's active equipment rentals
        context['badge_my_rentals'] = EquipmentRental.objects.filter(
            rented_by=user,
            status__in=['reserved', 'rented']
        ).count()

        # User's pending tournament registrations
        context['badge_my_tournaments'] = Registration.objects.filter(
            user=user,
            status='pending'
        ).count()

        # User's unread message replies (admin replied but user hasn't read)
        context['badge_user_messages'] = ContactMessage.objects.filter(
            email=user.email,
            admin_reply__isnull=False,
            user_read_reply=False
        ).count()

    return context


def sidebar_badges(request):
    """Context processor to add sidebar badge counts to all templates.
    Computed once per user and cached briefly (30s)."""
    if not request.user.is_authenticated:
        return {
            'badge_pending_reservations': 0,
            'badge_pending_payments': 0,
            'badge_pending_equipment': 0,
            'badge_pending_tournaments': 0,
            'badge_active_matches': 0,
            'badge_contact_messages': 0,
            'badge_my_pending_reservations': 0,
            'badge_my_pending_payments': 0,
            'badge_my_rentals': 0,
            'badge_my_tournaments': 0,
            'badge_user_messages': 0,
            'badge_pending_organizations': 0,
            'badge_pending_cancellations': 0,
            'badge_pending_refunds': 0,
        }

    try:
        cache = caches['pages']
        key = f'user_badges_{request.user.id}'
        context = cache.get(key)
        if context is None:
            context = _compute_badges(request.user)
            cache.set(key, context, _BADGES_TTL)
    except Exception:
        context = _compute_badges(request.user)
    return context
