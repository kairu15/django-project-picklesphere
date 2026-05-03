from django.db.models import Q
from reservations.models import Reservation
from equipment.models import EquipmentRental
from payments.models import Payment
from tournaments.models import Registration


def sidebar_badges(request):
    """Context processor to add sidebar badge counts to all templates"""
    context = {
        'badge_pending_reservations': 0,
        'badge_pending_payments': 0,
        'badge_pending_equipment': 0,
        'badge_pending_tournaments': 0,
        'badge_active_matches': 0,
        'badge_my_pending_reservations': 0,
        'badge_my_pending_payments': 0,
        'badge_my_rentals': 0,
        'badge_my_tournaments': 0,
    }
    
    if not request.user.is_authenticated:
        return context
    
    user = request.user
    
    # Admin badges
    if user.is_admin:
        # Pending reservations (pending status)
        context['badge_pending_reservations'] = Reservation.objects.filter(
            status='pending'
        ).count()
        
        # Pending payments (GCash payments that need verification)
        context['badge_pending_payments'] = Payment.objects.filter(
            status='pending',
            method='gcash'
        ).count()
        
        # Pending equipment rentals (reserved status, pending payment)
        context['badge_pending_equipment'] = EquipmentRental.objects.filter(
            status='reserved'
        ).count()
        
        # Tournament registrations pending
        context['badge_pending_tournaments'] = Registration.objects.filter(
            status='pending'
        ).count()
    
    # Staff badges
    elif user.is_staff_user:
        # Pending reservations for staff verification
        context['badge_pending_reservations'] = Reservation.objects.filter(
            status='pending'
        ).count()
        
        # Payments needing verification (pending GCash)
        context['badge_pending_payments'] = Payment.objects.filter(
            status='pending',
            method='gcash'
        ).count()
        
        # Equipment rentals needing checkout
        context['badge_pending_equipment'] = EquipmentRental.objects.filter(
            status='reserved',
            payment_status='paid'
        ).count()
    
    # Regular user badges
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
    
    return context
