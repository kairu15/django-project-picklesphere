from .models import Notification


def notification_count(request):
    """Context processor to add unread notification count and recent notifications to all templates."""
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False,
            is_deleted=False,
            is_archived=False,
        ).count()
        recent_notifications = Notification.objects.filter(
            user=request.user,
            is_deleted=False,
            is_archived=False,
        ).order_by('-created_at')[:5]
        return {
            'unread_notification_count': unread_count,
            'recent_notifications': recent_notifications,
        }
    return {
        'unread_notification_count': 0,
        'recent_notifications': [],
    }
