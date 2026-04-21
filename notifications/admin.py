from django.contrib import admin
from .models import Notification, BroadcastMessage


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'message']


@admin.register(BroadcastMessage)
class BroadcastMessageAdmin(admin.ModelAdmin):
    list_display = ['title', 'sent_by', 'sent_at', 'is_active']
    list_filter = ['is_active', 'sent_at']
