from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from accounts.decorators import admin_required, super_admin_required
from .models import Notification, BroadcastMessage


@login_required
def notification_list_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

    # Filter by read status
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'unread':
        notifications = notifications.filter(is_read=False)
    elif filter_type == 'read':
        notifications = notifications.filter(is_read=True)

    return render(request, 'user/notifications/notification_list.html', {
        'notifications': notifications,
        'filter_type': filter_type
    })


@login_required
def notification_detail_view(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)

    if not notification.is_read:
        notification.mark_as_read()

    return render(request, 'user/notifications/notification_detail.html', {
        'notification': notification
    })


@login_required
def mark_notification_read_view(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.mark_as_read()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, 'Notification marked as read.')
    return redirect('notification_list')


@login_required
def mark_all_read_view(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, 'All notifications marked as read.')
    return redirect('notification_list')


@login_required
def delete_notification_view(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, 'Notification deleted.')
    return redirect('notification_list')


@login_required
@super_admin_required
def broadcast_message_view(request):
    
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        target_roles = request.POST.getlist('target_roles')
        
        broadcast = BroadcastMessage.objects.create(
            title=title,
            message=message,
            sent_by=request.user,
            target_roles=target_roles
        )
        
        # Send to all users with specified roles
        from accounts.models import User
        users = User.objects.filter(role__in=target_roles)
        
        for user in users:
            Notification.objects.create(
                user=user,
                message=f"**{title}**: {message}",
                notification_type='info'
            )
        
        messages.success(request, f'Broadcast message sent to {users.count()} users.')
        return redirect('broadcast_list')
    
    return render(request, 'staff/notifications/broadcast_create.html')


@login_required
@super_admin_required
def broadcast_list_view(request):
    
    broadcasts = BroadcastMessage.objects.all().order_by('-sent_at')
    return render(request, 'staff/notifications/broadcast_list.html', {
        'broadcasts': broadcasts
    })
