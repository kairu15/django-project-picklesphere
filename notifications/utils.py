from django.utils import timezone
from django.db.models import Q
from .models import Notification, NotificationPreference


def create_notification(
    user,
    title='',
    message='',
    notification_type='info',
    category='system',
    priority='normal',
    action_url='',
    action_text='View Details',
    related_reservation=None,
    related_payment=None,
    related_match=None,
    related_organization=None,
    related_tournament=None,
    related_equipment=None,
    check_preferences=True,
    dedup_window_minutes=5,
):
    """
    Centralized notification creation with preference checking and deduplication.

    Args:
        user: The user to notify
        title: Short notification title
        message: Notification body text
        notification_type: info/success/warning/error
        category: reservation/payment/tournament/equipment/account/system/message/organization/maintenance/promotion
        priority: low/normal/high/urgent
        action_url: URL to redirect when notification is clicked
        action_text: Button text for the action link
        related_*: Related model instances
        check_preferences: Whether to check user's notification preferences
        dedup_window_minutes: Minutes within which duplicate notifications are prevented

    Returns:
        Notification instance or None if suppressed
    """
    if check_preferences:
        prefs = NotificationPreference.objects.filter(user=user).first()
        if prefs and not prefs.is_category_enabled(category):
            return None

    # Deduplication: check for similar notification in the time window
    if dedup_window_minutes > 0 and title:
        since = timezone.now() - timezone.timedelta(minutes=dedup_window_minutes)
        duplicate = Notification.objects.filter(
            user=user,
            title=title,
            category=category,
            created_at__gte=since
        ).first()
        if duplicate:
            return duplicate

    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        category=category,
        priority=priority,
        action_url=action_url,
        action_text=action_text,
        related_reservation=related_reservation,
        related_payment=related_payment,
        related_match=related_match,
        related_organization=related_organization,
        related_tournament=related_tournament,
        related_equipment=related_equipment,
    )
    return notification


def notify_reservation_submitted(user, reservation):
    """Notify user that a reservation was submitted"""
    return create_notification(
        user=user,
        title='Reservation Submitted',
        message=f'Your reservation for {reservation.court.name} on {reservation.date.strftime("%b %d, %Y")} has been submitted.',
        notification_type='info',
        category='reservation',
        priority='normal',
        action_url=f'/user/reservations/{reservation.id}/',
        action_text='View Reservation',
        related_reservation=reservation,
    )


def notify_reservation_approved(user, reservation):
    """Notify user that a reservation was approved"""
    return create_notification(
        user=user,
        title='Reservation Approved',
        message=f'Your reservation for {reservation.court.name} on {reservation.date.strftime("%b %d, %Y")} has been approved!',
        notification_type='success',
        category='reservation',
        priority='normal',
        action_url=f'/user/reservations/{reservation.id}/',
        action_text='View Reservation',
        related_reservation=reservation,
    )


def notify_reservation_confirmed(user, reservation):
    """Notify user that a reservation was confirmed"""
    return create_notification(
        user=user,
        title='Reservation Confirmed',
        message=f'Your reservation for {reservation.court.name} on {reservation.date.strftime("%b %d, %Y")} is confirmed.',
        notification_type='success',
        category='reservation',
        priority='normal',
        action_url=f'/user/reservations/{reservation.id}/',
        action_text='View Reservation',
        related_reservation=reservation,
    )


def notify_reservation_cancelled(user, reservation):
    """Notify user that a reservation was cancelled"""
    return create_notification(
        user=user,
        title='Reservation Cancelled',
        message=f'Your reservation for {reservation.court.name} on {reservation.date.strftime("%b %d, %Y")} has been cancelled.',
        notification_type='warning',
        category='reservation',
        priority='normal',
        action_url=f'/user/reservations/{reservation.id}/',
        action_text='View Details',
        related_reservation=reservation,
    )


def notify_payment_received(user, payment):
    """Notify user that a payment was received"""
    return create_notification(
        user=user,
        title='Payment Received',
        message=f'Your payment of ₱{payment.amount} for reservation #{payment.reservation.id} has been received.',
        notification_type='success',
        category='payment',
        priority='normal',
        action_url=f'/user/payments/',
        action_text='View Payments',
        related_payment=payment,
    )


def notify_payment_failed(user, payment):
    """Notify user that a payment failed"""
    return create_notification(
        user=user,
        title='Payment Failed',
        message=f'Your payment of ₱{payment.amount} could not be processed. Please try again.',
        notification_type='error',
        category='payment',
        priority='high',
        action_url=f'/user/payments/',
        action_text='Retry Payment',
        related_payment=payment,
    )


def notify_tournament_registration(user, tournament, status='pending'):
    """Notify user about tournament registration status"""
    if status == 'pending':
        title = 'Tournament Registration Submitted'
        msg = f'Your registration for {tournament.name} has been submitted and is pending approval.'
        ntype = 'info'
    elif status == 'approved':
        title = 'Tournament Registration Approved'
        msg = f'Your registration for {tournament.name} has been approved!'
        ntype = 'success'
    else:
        title = 'Tournament Registration Update'
        msg = f'Your registration for {tournament.name} status: {status}'
        ntype = 'info'

    return create_notification(
        user=user,
        title=title,
        message=msg,
        notification_type=ntype,
        category='tournament',
        priority='normal',
        action_url=f'/tournaments/{tournament.id}/',
        action_text='View Tournament',
        related_tournament=tournament,
    )


def notify_equipment_rental(user, equipment, status):
    """Notify user about equipment rental status"""
    status_msgs = {
        'reserved': f'Your rental for {equipment.name} has been reserved.',
        'rented': f'Your rental for {equipment.name} is now active.',
        'returned': f'Your rental for {equipment.name} has been returned successfully.',
        'cancelled': f'Your rental for {equipment.name} has been cancelled.',
    }
    msg = status_msgs.get(status, f'Equipment rental update for {equipment.name}.')
    title_map = {
        'reserved': 'Equipment Reserved',
        'rented': 'Equipment Rented',
        'returned': 'Equipment Returned',
        'cancelled': 'Equipment Rental Cancelled',
    }

    return create_notification(
        user=user,
        title=title_map.get(status, 'Equipment Update'),
        message=msg,
        notification_type='success' if status in ('returned',) else 'info',
        category='equipment',
        priority='normal',
        action_url=f'/equipment/{equipment.id}/',
        action_text='View Equipment',
        related_equipment=equipment,
    )


def notify_org_admin_new_reservation(admin_user, reservation):
    """Notify organization admin about a new reservation"""
    org = reservation.court.organization if hasattr(reservation.court, 'organization') else None
    return create_notification(
        user=admin_user,
        title='New Reservation Received',
        message=f'New reservation for {reservation.court.name} on {reservation.date.strftime("%b %d, %Y")} by {reservation.user.username}.',
        notification_type='info',
        category='reservation',
        priority='normal',
        action_url=f'/org-admin/reservations/',
        action_text='View Reservations',
        related_reservation=reservation,
        related_organization=org,
    )


def notify_super_admin_new_organization(super_admin, organization):
    """Notify super admin about a new organization registration"""
    return create_notification(
        user=super_admin,
        title='New Organization Registration',
        message=f'{organization.name} has registered and is awaiting approval.',
        notification_type='info',
        category='organization',
        priority='high',
        action_url=f'/super-admin/organizations/{organization.id}/',
        action_text='Review Organization',
        related_organization=organization,
    )


def notify_org_admin_cancellation_request(admin_user, cancellation):
    """Notify org admin about a cancellation request"""
    res = cancellation.reservation
    return create_notification(
        user=admin_user,
        title='Cancellation Request',
        message=f'{res.user.username} requested to cancel reservation for {res.court.name} on {res.date.strftime("%b %d, %Y")}.',
        notification_type='warning',
        category='reservation',
        priority='high',
        action_url=f'/org-admin/cancellations/',
        action_text='Review Cancellation',
        related_reservation=res,
    )


def notify_refund_processed(user, cancellation):
    """Notify user that their refund has been processed"""
    res = cancellation.reservation
    return create_notification(
        user=user,
        title='Refund Processed',
        message=f'Your refund for reservation #{res.id} ({res.court.name}) has been processed.',
        notification_type='success',
        category='payment',
        priority='normal',
        action_url=f'/user/payments/',
        action_text='View Payments',
        related_reservation=res,
    )


def notify_system_announcement(user, title, message, priority='normal'):
    """Send a system announcement to a user"""
    return create_notification(
        user=user,
        title=title,
        message=message,
        notification_type='info',
        category='system',
        priority=priority,
        action_text='Dismiss',
    )


def notify_maintenance_notice(user, title, message):
    """Send a maintenance notice"""
    return create_notification(
        user=user,
        title=title or 'Scheduled Maintenance',
        message=message or 'The system will undergo scheduled maintenance.',
        notification_type='warning',
        category='maintenance',
        priority='urgent',
    )


def broadcast_to_users(users, title, message, notification_type='info', category='system', priority='normal', action_url=''):
    """Send the same notification to multiple users efficiently"""
    notifications = []
    for user in users:
        n = create_notification(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            category=category,
            priority=priority,
            action_url=action_url,
        )
        if n:
            notifications.append(n)
    return notifications
