from django.contrib import admin
from .models import Notification, NotificationPreference, BroadcastMessage, NotificationTemplate


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'category', 'notification_type', 'priority', 'is_read', 'created_at']
    list_filter = ['notification_type', 'category', 'priority', 'is_read', 'is_archived', 'is_deleted', 'created_at']
    search_fields = ['user__username', 'user__email', 'title', 'message']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'read_at', 'archived_at']
    fieldsets = (
        ('User', {'fields': ['user']}),
        ('Content', {'fields': ['title', 'message']}),
        ('Classification', {'fields': ['notification_type', 'category', 'priority']}),
        ('Status', {'fields': ['is_read', 'is_archived', 'is_deleted', 'read_at', 'archived_at']}),
        ('Action', {'fields': ['action_url', 'action_text']}),
        ('Related Objects', {'fields': [
            'related_reservation', 'related_payment', 'related_match',
            'related_organization', 'related_tournament', 'related_equipment',
        ]}),
    )


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'frequency', 'email_notifications', 'push_notifications', 'updated_at']
    list_filter = ['frequency', 'email_notifications', 'push_notifications', 'sms_notifications']
    search_fields = ['user__username', 'user__email']


@admin.register(BroadcastMessage)
class BroadcastMessageAdmin(admin.ModelAdmin):
    list_display = ['title', 'sent_by', 'sent_at', 'status', 'target_type', 'recipient_count', 'is_active']
    list_filter = ['status', 'target_type', 'priority', 'is_active', 'sent_at']
    search_fields = ['title', 'message', 'sent_by__username']
    date_hierarchy = 'sent_at'
    readonly_fields = ['sent_at', 'recipient_count', 'read_count', 'click_count']
    fieldsets = (
        ('Content', {'fields': ['title', 'message']}),
        ('Sender', {'fields': ['sent_by']}),
        ('Delivery', {'fields': ['target_type', 'target_roles', 'target_organization', 'target_users']}),
        ('Classification', {'fields': ['notification_type', 'category', 'priority']}),
        ('Status', {'fields': ['status', 'is_active', 'scheduled_for', 'sent_at']}),
        ('Statistics', {'fields': ['recipient_count', 'read_count', 'click_count']}),
    )


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'notification_type', 'priority', 'is_active']
    list_filter = ['category', 'notification_type', 'priority', 'is_active']
    search_fields = ['name', 'title_template', 'message_template']
