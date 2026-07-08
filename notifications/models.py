from django.db import models
from django.utils import timezone
from django.conf import settings


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    )

    CATEGORY_CHOICES = (
        ('reservation', 'Reservation'),
        ('payment', 'Payment'),
        ('tournament', 'Tournament'),
        ('equipment', 'Equipment'),
        ('account', 'Account'),
        ('system', 'System'),
        ('message', 'Message'),
        ('organization', 'Organization'),
        ('maintenance', 'Maintenance'),
        ('promotion', 'Promotion'),
    )

    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=200, blank=True, default='')
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20, choices=NOTIFICATION_TYPES, default='info'
    )
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default='system'
    )
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default='normal'
    )
    is_read = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    # Action link (clicking notification goes here)
    action_url = models.CharField(max_length=500, blank=True, help_text='URL to redirect when clicked')
    action_text = models.CharField(max_length=100, blank=True, default='View Details')

    # Related objects (optional)
    related_reservation = models.ForeignKey(
        'reservations.Reservation', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    related_payment = models.ForeignKey(
        'payments.Payment', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    related_match = models.ForeignKey(
        'scoring.Match', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    related_organization = models.ForeignKey(
        'organizations.Organization', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    related_tournament = models.ForeignKey(
        'tournaments.Tournament', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    related_equipment = models.ForeignKey(
        'equipment.Equipment', on_delete=models.SET_NULL,
        null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read', '-created_at']),
            models.Index(fields=['user', 'category', '-created_at']),
        ]

    def __str__(self):
        return f"[{self.get_category_display()}] {self.user.username}: {self.title or self.message[:50]}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def archive(self):
        self.is_archived = True
        self.archived_at = timezone.now()
        self.save(update_fields=['is_archived', 'archived_at'])

    def restore(self):
        self.is_archived = False
        self.archived_at = None
        self.save(update_fields=['is_archived', 'archived_at'])

    @property
    def icon_class(self):
        icons = {
            'reservation': 'fa-calendar-check',
            'payment': 'fa-credit-card',
            'tournament': 'fa-trophy',
            'equipment': 'fa-tools',
            'account': 'fa-user',
            'system': 'fa-cog',
            'message': 'fa-envelope',
            'organization': 'fa-building',
            'maintenance': 'fa-shield-alt',
            'promotion': 'fa-tags',
        }
        return icons.get(self.category, 'fa-bell')

    @property
    def time_display(self):
        now = timezone.now()
        diff = now - self.created_at
        if diff.days == 0:
            if diff.seconds < 60:
                return 'Just now'
            elif diff.seconds < 3600:
                return f'{diff.seconds // 60}m ago'
            else:
                return f'{diff.seconds // 3600}h ago'
        elif diff.days == 1:
            return 'Yesterday'
        elif diff.days < 7:
            return f'{diff.days}d ago'
        elif diff.days < 30:
            return f'{diff.days // 7}w ago'
        elif diff.days < 365:
            return f'{diff.days // 30}mo ago'
        else:
            return f'{diff.days // 365}y ago'

    @property
    def group_key(self):
        """Returns a grouping key for today/yesterday/this week/earlier"""
        now = timezone.now()
        if self.created_at.date() == now.date():
            return 'Today'
        elif self.created_at.date() == (now - timezone.timedelta(days=1)).date():
            return 'Yesterday'
        elif self.created_at.date() >= (now - timezone.timedelta(days=7)).date():
            return 'This Week'
        else:
            return 'Earlier'


class NotificationPreference(models.Model):
    FREQUENCY_CHOICES = (
        ('instant', 'Instant'),
        ('hourly', 'Hourly Digest'),
        ('daily', 'Daily Digest'),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )

    # Category toggles
    notify_reservation = models.BooleanField(default=True)
    notify_payment = models.BooleanField(default=True)
    notify_tournament = models.BooleanField(default=True)
    notify_equipment = models.BooleanField(default=True)
    notify_account = models.BooleanField(default=True)
    notify_system = models.BooleanField(default=True)
    notify_message = models.BooleanField(default=True)
    notify_organization = models.BooleanField(default=True)
    notify_maintenance = models.BooleanField(default=True)
    notify_promotion = models.BooleanField(default=False)

    # Delivery methods
    email_notifications = models.BooleanField(default=False, help_text='Receive email notifications')
    push_notifications = models.BooleanField(default=False, help_text='Receive browser push notifications')
    sms_notifications = models.BooleanField(default=False, help_text='Receive SMS notifications')

    # Frequency
    frequency = models.CharField(
        max_length=10, choices=FREQUENCY_CHOICES, default='instant'
    )

    # Quiet hours
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_preferences'
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'

    def __str__(self):
        return f'Preferences for {self.user.username}'

    def is_category_enabled(self, category):
        """Check if a notification category is enabled for this user"""
        field_map = {
            'reservation': 'notify_reservation',
            'payment': 'notify_payment',
            'tournament': 'notify_tournament',
            'equipment': 'notify_equipment',
            'account': 'notify_account',
            'system': 'notify_system',
            'message': 'notify_message',
            'organization': 'notify_organization',
            'maintenance': 'notify_maintenance',
            'promotion': 'notify_promotion',
        }
        field = field_map.get(category)
        if field:
            return getattr(self, field, True)
        return True


class BroadcastMessage(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='broadcasts'
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    # Target audience
    target_roles = models.JSONField(default=list)
    target_type = models.CharField(
        max_length=20,
        choices=[
            ('all', 'All Users'),
            ('roles', 'Specific Roles'),
            ('organization', 'Specific Organization'),
        ],
        default='all'
    )
    target_organization = models.ForeignKey(
        'organizations.Organization', on_delete=models.SET_NULL,
        null=True, blank=True
    )

    # Priority
    priority = models.CharField(
        max_length=10, choices=Notification.PRIORITY_CHOICES,
        default='normal'
    )

    recipient_count = models.IntegerField(default=0, help_text='Number of users who received this')
    read_count = models.IntegerField(default=0, help_text='Number of users who have read this')

    class Meta:
        db_table = 'broadcast_messages'
        ordering = ['-sent_at']

    def __str__(self):
        return f"Broadcast: {self.title}"
