from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from accounts.decorators import admin_required, super_admin_required
from .models import Notification, NotificationPreference, BroadcastMessage
from .utils import broadcast_to_users


@login_required
def notification_list_view(request):
    """Enhanced notification list with search, filter, sort, and grouping"""
    notifications = Notification.objects.filter(
        user=request.user,
        is_deleted=False
    )

    # Search
    search_query = request.GET.get('search', '').strip()
    if search_query:
        notifications = notifications.filter(
            Q(title__icontains=search_query) |
            Q(message__icontains=search_query)
        )

    # Filter by type
    type_filter = request.GET.get('type', '')
    if type_filter:
        notifications = notifications.filter(notification_type=type_filter)

    # Filter by category
    category_filter = request.GET.get('category', '')
    if category_filter:
        notifications = notifications.filter(category=category_filter)

    # Filter by read status
    status_filter = request.GET.get('status', '')
    if status_filter == 'unread':
        notifications = notifications.filter(is_read=False)
    elif status_filter == 'read':
        notifications = notifications.filter(is_read=True)

    # Filter by archive status
    archive_filter = request.GET.get('archive', '')
    if archive_filter == 'archived':
        notifications = notifications.filter(is_archived=True)
    else:
        notifications = notifications.filter(is_archived=False)

    # Filter by priority
    priority_filter = request.GET.get('priority', '')
    if priority_filter:
        notifications = notifications.filter(priority=priority_filter)

    # Filter by date
    date_filter = request.GET.get('date', '')
    today = timezone.now().date()
    if date_filter == 'today':
        notifications = notifications.filter(created_at__date=today)
    elif date_filter == 'yesterday':
        notifications = notifications.filter(created_at__date=today - timezone.timedelta(days=1))
    elif date_filter == 'week':
        notifications = notifications.filter(created_at__date__gte=today - timezone.timedelta(days=7))
    elif date_filter == 'month':
        notifications = notifications.filter(created_at__date__gte=today - timezone.timedelta(days=30))

    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    allowed_sorts = ['created_at', '-created_at', 'priority', '-priority', 'category', '-category', 'notification_type', '-notification_type']
    if sort_by not in allowed_sorts:
        sort_by = '-created_at'
    notifications = notifications.order_by(sort_by)

    # Stats
    total_count = notifications.count()
    unread_count = Notification.objects.filter(
        user=request.user, is_read=False, is_deleted=False, is_archived=False
    ).count()

    # Group notifications by time period
    grouped = {'Today': [], 'Yesterday': [], 'This Week': [], 'Earlier': []}
    for n in notifications:
        grouped.setdefault(n.group_key, []).append(n)

    # Paginate - use the flat list for pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Get category counts for filter sidebar
    category_counts = Notification.objects.filter(
        user=request.user, is_deleted=False, is_archived=False
    ).values('category').annotate(count=Count('id')).order_by('-count')

    context = {
        'notifications': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'search_query': search_query,
        'type_filter': type_filter,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'archive_filter': archive_filter,
        'priority_filter': priority_filter,
        'date_filter': date_filter,
        'sort_by': sort_by,
        'total_count': total_count,
        'unread_count': unread_count,
        'category_counts': category_counts,
        'selected_ids': request.GET.getlist('selected'),
    }

    return render(request, 'user/notifications/notification_list.html', context)


@login_required
def notification_detail_view(request, notification_id):
    notification = get_object_or_404(
        Notification, id=notification_id, user=request.user
    )

    if not notification.is_read:
        notification.mark_as_read()

    return render(request, 'user/notifications/notification_detail.html', {
        'notification': notification
    })


@login_required
def mark_notification_read_view(request, notification_id):
    notification = get_object_or_404(
        Notification, id=notification_id, user=request.user
    )
    notification.mark_as_read()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    messages.success(request, 'Notification marked as read.')
    return redirect('notification_list')


@login_required
def mark_all_read_view(request):
    count = Notification.objects.filter(
        user=request.user, is_read=False
    ).update(is_read=True, read_at=timezone.now())

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'count': count})

    messages.success(request, f'{count} notification(s) marked as read.')
    return redirect('notification_list')


@login_required
def delete_notification_view(request, notification_id):
    notification = get_object_or_404(
        Notification, id=notification_id, user=request.user
    )
    notification.is_deleted = True
    notification.save(update_fields=['is_deleted'])

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    messages.success(request, 'Notification deleted.')
    return redirect('notification_list')


@login_required
def delete_selected_notifications_view(request):
    if request.method == 'POST':
        ids = request.POST.getlist('notification_ids')
        if ids:
            count = Notification.objects.filter(
                id__in=ids, user=request.user
            ).update(is_deleted=True)
            messages.success(request, f'{count} notification(s) deleted.')
        return redirect('notification_list')
    return redirect('notification_list')


@login_required
def clear_all_notifications_view(request):
    if request.method == 'POST':
        count = Notification.objects.filter(
            user=request.user, is_deleted=False
        ).update(is_deleted=True)
        messages.success(request, f'Cleared {count} notification(s).')
        return redirect('notification_list')
    return redirect('notification_list')


@login_required
def archive_notification_view(request, notification_id):
    notification = get_object_or_404(
        Notification, id=notification_id, user=request.user
    )
    notification.archive()
    messages.success(request, 'Notification archived.')
    return redirect('notification_list')


@login_required
def restore_notification_view(request, notification_id):
    notification = get_object_or_404(
        Notification, id=notification_id, user=request.user
    )
    notification.restore()
    messages.success(request, 'Notification restored.')
    return redirect('notification_list')


@login_required
def notification_preferences_view(request):
    """View and update notification preferences"""
    prefs, created = NotificationPreference.objects.get_or_create(
        user=request.user
    )

    if request.method == 'POST':
        # Category toggles
        prefs.notify_reservation = request.POST.get('notify_reservation') == 'on'
        prefs.notify_payment = request.POST.get('notify_payment') == 'on'
        prefs.notify_tournament = request.POST.get('notify_tournament') == 'on'
        prefs.notify_equipment = request.POST.get('notify_equipment') == 'on'
        prefs.notify_account = request.POST.get('notify_account') == 'on'
        prefs.notify_system = request.POST.get('notify_system') == 'on'
        prefs.notify_message = request.POST.get('notify_message') == 'on'
        prefs.notify_organization = request.POST.get('notify_organization') == 'on'
        prefs.notify_maintenance = request.POST.get('notify_maintenance') == 'on'
        prefs.notify_promotion = request.POST.get('notify_promotion') == 'on'

        # Delivery methods
        prefs.email_notifications = request.POST.get('email_notifications') == 'on'
        prefs.push_notifications = request.POST.get('push_notifications') == 'on'
        prefs.sms_notifications = request.POST.get('sms_notifications') == 'on'

        # Frequency
        prefs.frequency = request.POST.get('frequency', 'instant')

        # Quiet hours
        start = request.POST.get('quiet_hours_start')
        end = request.POST.get('quiet_hours_end')
        if start and end:
            from datetime import datetime
            prefs.quiet_hours_start = datetime.strptime(start, '%H:%M').time()
            prefs.quiet_hours_end = datetime.strptime(end, '%H:%M').time()
        else:
            prefs.quiet_hours_start = None
            prefs.quiet_hours_end = None

        prefs.save()
        messages.success(request, 'Notification preferences updated!')
        return redirect('notification_preferences')

    return render(request, 'user/notifications/notification_preferences.html', {
        'prefs': prefs,
    })


@login_required
def get_unread_count_api(request):
    """API endpoint for real-time unread count (polled by frontend)"""
    count = Notification.objects.filter(
        user=request.user, is_read=False, is_deleted=False, is_archived=False
    ).count()

    recent = Notification.objects.filter(
        user=request.user, is_deleted=False, is_archived=False
    ).order_by('-created_at')[:3]

    data = {
        'unread_count': count,
        'recent': [{
            'id': n.id,
            'title': n.title,
            'message': n.message[:80],
            'type': n.notification_type,
            'category': n.category,
            'time': n.time_display,
            'is_read': n.is_read,
            'action_url': n.action_url or '',
        } for n in recent]
    }
    return JsonResponse(data)


# ==================== SUPER ADMIN BROADCAST ====================

@login_required
@super_admin_required
def broadcast_message_view(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        target_type = request.POST.get('target_type', 'all')
        target_roles = request.POST.getlist('target_roles')
        priority = request.POST.get('priority', 'normal')
        category = request.POST.get('category', 'system')

        from accounts.models import User

        users = User.objects.filter(is_active=True)
        if target_type == 'roles' and target_roles:
            users = users.filter(role__in=target_roles)
        elif target_type == 'organization':
            org_id = request.POST.get('target_organization')
            if org_id:
                users = users.filter(organization_id=org_id)

        # Create the broadcast record
        broadcast = BroadcastMessage.objects.create(
            title=title,
            message=message,
            sent_by=request.user,
            target_roles=target_roles,
            target_type=target_type,
            priority=priority,
            recipient_count=users.count(),
        )

        # Send notifications
        sent = broadcast_to_users(
            users, title, message,
            notification_type='info',
            category=category or 'system',
            priority=priority,
        )

        messages.success(
            request,
            f'Broadcast sent to {len(sent)} users.'
        )
        return redirect('broadcast_list')

    from organizations.models import Organization
    orgs = Organization.objects.filter(is_active=True)
    return render(request, 'staff/notifications/broadcast_create.html', {
        'organizations': orgs,
    })


@login_required
@super_admin_required
def broadcast_list_view(request):
    broadcasts = BroadcastMessage.objects.all().order_by('-sent_at')
    return render(request, 'staff/notifications/broadcast_list.html', {
        'broadcasts': broadcasts
    })


@login_required
@super_admin_required
def broadcast_detail_view(request, broadcast_id):
    broadcast = get_object_or_404(BroadcastMessage, id=broadcast_id)
    return render(request, 'staff/notifications/broadcast_detail.html', {
        'broadcast': broadcast
    })
