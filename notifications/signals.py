from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import user_logged_in, user_login_failed
from django.utils import timezone

from .models import Notification
from .utils import (
    create_notification,
    notify_reservation_submitted,
    notify_reservation_approved,
    notify_reservation_confirmed,
    notify_reservation_cancelled,
    notify_payment_received,
    notify_payment_failed,
    notify_tournament_registration,
    notify_equipment_rental,
    notify_org_admin_new_reservation,
    notify_super_admin_new_organization,
    notify_org_admin_cancellation_request,
    notify_refund_processed,
)
from accounts.models import User


# ==================== RESERVATION SIGNALS ====================

@receiver(post_save, sender='reservations.Reservation')
def reservation_saved_handler(sender, instance, created, **kwargs):
    """Generate notifications when reservation status changes"""
    user = instance.user

    try:
        if created:
            # Notify the user
            notify_reservation_submitted(user, instance)
            # Notify org admin/staff
            org_admins = User.objects.filter(
                organization=instance.court.organization,
                role__in=['org_admin', 'org_staff']
            )
            for admin in org_admins:
                notify_org_admin_new_reservation(admin, instance)
            return

        # Check if this is a status update (we need to track previous status)
        if hasattr(instance, '_old_status'):
            old_status = instance._old_status
            new_status = instance.status

            if old_status != new_status:
                if new_status == 'confirmed':
                    notify_reservation_confirmed(user, instance)
                elif new_status == 'cancelled':
                    notify_reservation_cancelled(user, instance)
    except Exception:
        # Don't let signal failures break the main operation
        pass


@receiver(pre_save, sender='reservations.Reservation')
def reservation_pre_save_handler(sender, instance, **kwargs):
    """Store the old status value for change detection"""
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            instance._old_status = old.status
        except sender.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


# ==================== PAYMENT SIGNALS ====================

@receiver(post_save, sender='payments.Payment')
def payment_saved_handler(sender, instance, created, **kwargs):
    """Generate notifications when payment is created or status changes"""
    try:
        user = instance.reservation.user if instance.reservation else None
        if not user:
            return

        if created:
            notify_payment_received(user, instance)
            return

        if hasattr(instance, '_old_status'):
            old_status = instance._old_status
            new_status = instance.status
            if old_status != new_status and new_status in ('failed', 'rejected'):
                notify_payment_failed(user, instance)
    except Exception:
        pass


@receiver(pre_save, sender='payments.Payment')
def payment_pre_save_handler(sender, instance, **kwargs):
    """Store the old status value for change detection"""
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            instance._old_status = old.status
        except sender.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


# ==================== TOURNAMENT SIGNALS ====================

@receiver(post_save, sender='tournaments.Registration')
def tournament_registration_handler(sender, instance, created, **kwargs):
    """Generate notifications for tournament registrations"""
    try:
        status = 'pending' if instance.status == 'pending' else instance.status
        notify_tournament_registration(
            instance.user, instance.tournament, status
        )
    except Exception:
        pass


# ==================== EQUIPMENT RENTAL SIGNALS ====================

@receiver(post_save, sender='equipment.EquipmentRental')
def equipment_rental_handler(sender, instance, created, **kwargs):
    """Generate notifications for equipment rental status changes"""
    try:
        if created:
            status = 'reserved' if instance.status == 'reserved' else instance.status
        else:
            if hasattr(instance, '_old_status'):
                status = instance.status
            else:
                return

        notify_equipment_rental(instance.rented_by, instance.equipment, status)
    except Exception:
        pass


# ==================== ORGANIZATION SIGNALS ====================

@receiver(post_save, sender='organizations.Organization')
def organization_saved_handler(sender, instance, created, **kwargs):
    """Notify super admins when a new organization registers"""
    try:
        if created and instance.status == 'pending':
            super_admins = User.objects.filter(role='super_admin', is_active=True)
            for admin in super_admins:
                notify_super_admin_new_organization(admin, instance)
    except Exception:
        pass


# ==================== CANCELLATION SIGNALS ====================

@receiver(post_save, sender='reservations.CancellationRequest')
def cancellation_request_handler(sender, instance, created, **kwargs):
    """Notify org admin about cancellation requests"""
    try:
        if created:
            reservation = instance.reservation
            org_admins = User.objects.filter(
                organization=reservation.court.organization,
                role__in=['org_admin', 'org_staff']
            )
            for admin in org_admins:
                notify_org_admin_cancellation_request(admin, instance)

        # If approved and refunded, notify the user
        if instance.approved and instance.refund_processed:
            notify_refund_processed(
                instance.reservation.user, instance
            )
    except Exception:
        pass


# ==================== LOGIN SIGNALS ====================

@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """Track successful login"""
    request.session['last_login'] = timezone.now().isoformat()


@receiver(user_login_failed)
def user_login_failed_handler(sender, credentials, request, **kwargs):
    """Notify super admins about failed login attempts"""
    try:
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()

        username = credentials.get('username', '')
        if username:
            super_admins = User.objects.filter(role='super_admin', is_active=True)
            for admin in super_admins:
                create_notification(
                    user=admin,
                    title='Failed Login Attempt',
                    message=f'A failed login attempt was detected for username: {username}',
                    notification_type='warning',
                    category='system',
                    priority='high',
                )
    except Exception:
        pass


# ==================== APPS READY ====================

def connect_signals():
    """Connect all signals - called from apps.py ready()"""
    # Signals are connected via @receiver decorators automatically
    # when Django imports the signals module
    pass
