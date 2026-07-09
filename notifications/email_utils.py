"""
Email utility module for PickleSphere transactional emails.
Uses django-anymail with Elastic Email backend in production,
falls back to console backend in development.
"""
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse


def _get_user_email_prefs(user):
    """Check if the user has email notifications enabled."""
    try:
        prefs = user.notification_preferences
        return prefs.email_notifications
    except Exception:
        return False


def send_transactional_email(
    user,
    subject,
    template_name,
    context=None,
    cc=None,
    bcc=None,
    reply_to=None,
):
    """
    Send an HTML email to a user using a template.
    
    Args:
        user: User object (must have email)
        subject: Email subject line
        template_name: Path to HTML template (e.g., 'emails/reservation_confirmed.html')
        context: Dict of template context variables
        cc: List of CC email addresses
        bcc: List of BCC email addresses
        reply_to: List of reply-to addresses
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    if not user.email:
        return False

    if context is None:
        context = {}
    
    # Add common context
    context.setdefault('user', user)
    context.setdefault('site_name', settings.SITE_NAME)
    context.setdefault('site_url', settings.SITE_URL)
    context.setdefault('unsubscribe_url', settings.SITE_URL + '/user/notifications/preferences/')

    try:
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)
        
        msg = EmailMultiAlternatives(
            subject=f'[{settings.SITE_NAME}] {subject}',
            body=text_content,
            from_email=f'{settings.DEFAULT_FROM_NAME} <{settings.DEFAULT_FROM_EMAIL}>',
            to=[user.email],
            cc=cc or [],
            bcc=bcc or [],
            reply_to=reply_to or [settings.DEFAULT_FROM_EMAIL],
        )
        msg.attach_alternative(html_content, 'text/html')
        msg.send()
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Failed to send email to {user.email}: {e}')
        return False


def send_notification_email(user, notification_obj=None, **context_overrides):
    """
    Send an email notification based on a Notification object or explicit context.
    
    Args:
        user: User to send to
        notification_obj: Optional Notification model instance
        **context_overrides: Additional template context
    """
    if not _get_user_email_prefs(user):
        return False
    
    title = context_overrides.get('title', '')
    message = context_overrides.get('message', '')
    category = context_overrides.get('category', 'system')
    
    if notification_obj:
        title = title or notification_obj.title
        message = message or notification_obj.message
        category = category or notification_obj.category

    context = {
        'title': title,
        'message': message,
        'category': category,
        'notification_type': context_overrides.get('notification_type', 'info'),
        'action_url': context_overrides.get('action_url', ''),
        'action_text': context_overrides.get('action_text', 'View Details'),
        **context_overrides,
    }
    
    return send_transactional_email(
        user=user,
        subject=title or 'PickleSphere Notification',
        template_name='emails/notification.html',
        context=context,
    )


# ==================== SPECIFIC EMAIL HELPERS ====================

def send_reservation_confirmed_email(user, reservation):
    """Send reservation confirmation email."""
    return send_transactional_email(
        user=user,
        subject='Reservation Confirmed!',
        template_name='emails/reservation_confirmed.html',
        context={
            'title': 'Reservation Confirmed!',
            'reservation': reservation,
            'court_name': reservation.court.name,
            'date': reservation.date.strftime('%A, %B %d, %Y'),
            'start_time': reservation.start_time.strftime('%I:%M %p'),
            'end_time': reservation.end_time.strftime('%I:%M %p'),
            'reservation_id': reservation.id,
            'amount': getattr(reservation, 'amount', 'N/A'),
            'action_url': f'{settings.SITE_URL}/user/reservations/{reservation.id}/',
            'action_text': 'View Reservation',
        },
    )


def send_reservation_submitted_email(user, reservation):
    """Send reservation submitted (pending) email."""
    return send_transactional_email(
        user=user,
        subject='Reservation Submitted',
        template_name='emails/reservation_submitted.html',
        context={
            'title': 'Reservation Submitted',
            'reservation': reservation,
            'court_name': reservation.court.name,
            'date': reservation.date.strftime('%A, %B %d, %Y'),
            'start_time': reservation.start_time.strftime('%I:%M %p'),
            'end_time': reservation.end_time.strftime('%I:%M %p'),
            'reservation_id': reservation.id,
            'action_url': f'{settings.SITE_URL}/user/reservations/{reservation.id}/',
            'action_text': 'View Reservation',
        },
    )


def send_reservation_cancelled_email(user, reservation):
    """Send reservation cancellation email."""
    return send_transactional_email(
        user=user,
        subject='Reservation Cancelled',
        template_name='emails/reservation_cancelled.html',
        context={
            'title': 'Reservation Cancelled',
            'reservation': reservation,
            'court_name': reservation.court.name,
            'date': reservation.date.strftime('%A, %B %d, %Y'),
            'reservation_id': reservation.id,
            'action_url': f'{settings.SITE_URL}/user/reservations/{reservation.id}/',
            'action_text': 'View Details',
        },
    )


def send_payment_confirmed_email(user, payment):
    """Send payment confirmation email."""
    return send_transactional_email(
        user=user,
        subject='Payment Confirmed!',
        template_name='emails/payment_confirmed.html',
        context={
            'title': 'Payment Confirmed!',
            'payment': payment,
            'amount': payment.amount,
            'method': payment.get_method_display() if hasattr(payment, 'get_method_display') else payment.method,
            'reference': payment.reference or f'#{payment.id}',
            'payment_id': payment.id,
            'reservation': payment.reservation,
            'action_url': f'{settings.SITE_URL}/user/payments/',
            'action_text': 'View Payments',
        },
    )


def send_refund_processed_email(user, cancellation):
    """Send refund processed email."""
    res = cancellation.reservation
    return send_transactional_email(
        user=user,
        subject='Refund Processed',
        template_name='emails/refund_processed.html',
        context={
            'title': 'Refund Processed',
            'cancellation': cancellation,
            'reservation': res,
            'court_name': res.court.name,
            'date': res.date.strftime('%A, %B %d, %Y'),
            'reservation_id': res.id,
            'action_url': f'{settings.SITE_URL}/user/payments/',
            'action_text': 'View Payments',
        },
    )


def send_tournament_registration_email(user, tournament, status='pending'):
    """Send tournament registration status email."""
    subject_map = {
        'pending': 'Tournament Registration Submitted',
        'approved': 'Tournament Registration Approved!',
        'rejected': 'Tournament Registration Update',
    }
    return send_transactional_email(
        user=user,
        subject=subject_map.get(status, 'Tournament Registration Update'),
        template_name='emails/tournament_registration.html',
        context={
            'title': subject_map.get(status, 'Tournament Registration Update'),
            'tournament': tournament,
            'tournament_name': tournament.name,
            'status': status,
            'action_url': f'{settings.SITE_URL}/user/tournaments/',
            'action_text': 'View Tournaments',
        },
    )


def send_equipment_rental_email(user, equipment, status):
    """Send equipment rental status email."""
    status_labels = {
        'reserved': 'Equipment Reserved',
        'rented': 'Equipment Ready for Pickup',
        'returned': 'Equipment Returned',
        'cancelled': 'Equipment Rental Cancelled',
        'overdue': 'Equipment Overdue!',
    }
    return send_transactional_email(
        user=user,
        subject=status_labels.get(status, 'Equipment Update'),
        template_name='emails/equipment_rental.html',
        context={
            'title': status_labels.get(status, 'Equipment Update'),
            'equipment': equipment,
            'equipment_name': equipment.name,
            'status': status,
            'action_url': f'{settings.SITE_URL}/equipment/{equipment.id}/',
            'action_text': 'View Equipment',
        },
    )


def send_account_update_email(user, message_text):
    """Send account update notification email."""
    return send_transactional_email(
        user=user,
        subject='Account Updated',
        template_name='emails/account_update.html',
        context={
            'title': 'Account Updated',
            'message_text': message_text,
            'action_url': f'{settings.SITE_URL}/accounts/profile/',
            'action_text': 'View Profile',
        },
    )


def send_password_reset_email(user, reset_url):
    """Send password reset email."""
    return send_transactional_email(
        user=user,
        subject='Password Reset Request',
        template_name='emails/password_reset.html',
        context={
            'title': 'Password Reset',
            'reset_url': reset_url,
            'action_url': reset_url,
            'action_text': 'Reset Password',
            'expires_in': '1 hour',
        },
    )


def send_welcome_email(user):
    """Send welcome email to new users."""
    return send_transactional_email(
        user=user,
        subject='Welcome to PickleSphere!',
        template_name='emails/welcome.html',
        context={
            'title': 'Welcome to PickleSphere!',
            'username': user.username,
            'action_url': f'{settings.SITE_URL}/',
            'action_text': 'Get Started',
        },
    )


def send_org_status_change_email(user, organization, new_status, note=''):
    """Send organization status change email."""
    status_labels = {
        'approved': 'Organization Approved!',
        'rejected': 'Organization Status Update',
        'suspended': 'Organization Suspended',
        'pending': 'Organization Status Update',
    }
    return send_transactional_email(
        user=user,
        subject=status_labels.get(new_status, 'Organization Update'),
        template_name='emails/organization_status.html',
        context={
            'title': status_labels.get(new_status, 'Organization Update'),
            'organization': organization,
            'organization_name': organization.name,
            'new_status': new_status,
            'note': note,
            'action_url': f'{settings.SITE_URL}/org-admin/dashboard/',
            'action_text': 'Go to Dashboard',
        },
    )


def send_test_email(user):
    """Send a test email to verify configuration."""
    return send_transactional_email(
        user=user,
        subject='Test Email from PickleSphere',
        template_name='emails/test_email.html',
        context={
            'title': 'Test Email',
            'message': 'If you received this email, your email configuration is working correctly!',
        },
    )
