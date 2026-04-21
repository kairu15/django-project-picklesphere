from django.db import models
from accounts.models import User


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    is_read = models.BooleanField(default=False)
    
    # Related objects (optional)
    related_reservation = models.ForeignKey('reservations.Reservation', on_delete=models.CASCADE, null=True, blank=True)
    related_payment = models.ForeignKey('payments.Payment', on_delete=models.CASCADE, null=True, blank=True)
    related_match = models.ForeignKey('scoring.Match', on_delete=models.CASCADE, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:50]}..."
    
    def mark_as_read(self):
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


class BroadcastMessage(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    sent_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='broadcasts')
    sent_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # Target audience
    target_roles = models.JSONField(default=list)  # ['user', 'staff', 'admin']
    
    class Meta:
        db_table = 'broadcast_messages'
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"Broadcast: {self.title}"
