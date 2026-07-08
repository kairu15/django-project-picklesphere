from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.messages.storage.fallback import FallbackStorage
from django.utils import timezone
from datetime import timedelta

from accounts.models import User
from .models import Notification, NotificationPreference, BroadcastMessage, NotificationTemplate


# ==================== MODEL TESTS ====================

class NotificationModelTests(TestCase):
    """Tests for the Notification model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='test123', role='user'
        )
        self.notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='This is a test notification message.',
            notification_type='info',
            category='system',
            priority='normal',
        )

    def test_notification_creation(self):
        self.assertEqual(self.notification.title, 'Test Notification')
        self.assertEqual(self.notification.message, 'This is a test notification message.')
        self.assertEqual(self.notification.notification_type, 'info')
        self.assertEqual(self.notification.category, 'system')
        self.assertEqual(self.notification.priority, 'normal')
        self.assertFalse(self.notification.is_read)
        self.assertFalse(self.notification.is_archived)
        self.assertFalse(self.notification.is_deleted)

    def test_str_representation(self):
        expected = '[System] testuser: Test Notification'
        self.assertEqual(str(self.notification), expected)

    def test_mark_as_read(self):
        self.notification.mark_as_read()
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)
        self.assertIsNotNone(self.notification.read_at)

    def test_mark_as_read_idempotent(self):
        self.notification.mark_as_read()
        read_at_1 = self.notification.read_at
        self.notification.mark_as_read()
        read_at_2 = self.notification.read_at
        self.assertEqual(read_at_1, read_at_2)

    def test_mark_as_unread(self):
        self.notification.mark_as_read()
        self.notification.mark_as_unread()
        self.notification.refresh_from_db()
        self.assertFalse(self.notification.is_read)
        self.assertIsNone(self.notification.read_at)

    def test_archive_and_restore(self):
        self.notification.archive()
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_archived)
        self.assertIsNotNone(self.notification.archived_at)

        self.notification.restore()
        self.notification.refresh_from_db()
        self.assertFalse(self.notification.is_archived)
        self.assertIsNone(self.notification.archived_at)

    def test_time_display_just_now(self):
        """Notification created moments ago should show 'Just now'."""
        self.assertEqual(self.notification.time_display, 'Just now')

    def test_time_display_minutes_ago(self):
        self.notification.created_at = timezone.now() - timedelta(minutes=5)
        self.assertEqual(self.notification.time_display, '5m ago')

    def test_time_display_hours_ago(self):
        self.notification.created_at = timezone.now() - timedelta(hours=3)
        self.assertEqual(self.notification.time_display, '3h ago')

    def test_time_display_yesterday(self):
        self.notification.created_at = timezone.now() - timedelta(days=1)
        self.assertEqual(self.notification.time_display, 'Yesterday')

    def test_time_display_days_ago(self):
        self.notification.created_at = timezone.now() - timedelta(days=3)
        self.assertEqual(self.notification.time_display, '3d ago')

    def test_time_display_weeks_ago(self):
        self.notification.created_at = timezone.now() - timedelta(days=14)
        self.assertEqual(self.notification.time_display, '2w ago')

    def test_time_display_months_ago(self):
        self.notification.created_at = timezone.now() - timedelta(days=60)
        self.assertEqual(self.notification.time_display, '2mo ago')

    def test_group_key_today(self):
        self.assertEqual(self.notification.group_key, 'Today')

    def test_group_key_yesterday(self):
        self.notification.created_at = timezone.now() - timedelta(days=1)
        self.assertEqual(self.notification.group_key, 'Yesterday')

    def test_group_key_this_week(self):
        self.notification.created_at = timezone.now() - timedelta(days=3)
        self.assertEqual(self.notification.group_key, 'This Week')

    def test_group_key_earlier(self):
        self.notification.created_at = timezone.now() - timedelta(days=8)
        self.assertEqual(self.notification.group_key, 'Earlier')

    def test_icon_class_all_categories(self):
        category_icons = {
            'reservation': 'fa-calendar-check',
            'payment': 'fa-credit-card',
            'refund': 'fa-undo-alt',
            'cancellation': 'fa-times-circle',
            'tournament': 'fa-trophy',
            'equipment': 'fa-tools',
            'organization': 'fa-building',
            'staff': 'fa-users-gear',
            'user': 'fa-user',
            'report': 'fa-chart-bar',
            'system': 'fa-cog',
            'security': 'fa-shield-alt',
            'maintenance': 'fa-wrench',
            'announcement': 'fa-bullhorn',
            'promotion': 'fa-tags',
            'message': 'fa-envelope',
            'account': 'fa-user-circle',
        }
        for category, expected_icon in category_icons.items():
            self.notification.category = category
            self.assertEqual(self.notification.icon_class, expected_icon)

    def test_category_color_all_categories(self):
        category_colors = {
            'reservation': '#3B7A8C',
            'payment': '#28a745',
            'refund': '#fd7e14',
            'cancellation': '#dc3545',
            'tournament': '#ffc107',
            'equipment': '#6f42c1',
            'organization': '#20c997',
            'staff': '#e83e8c',
            'user': '#17a2b8',
            'report': '#6c757d',
            'system': '#343a40',
            'security': '#dc3545',
            'maintenance': '#ffc107',
            'announcement': '#0d6efd',
            'promotion': '#fd7e14',
            'message': '#e83e8c',
            'account': '#17a2b8',
        }
        for category, expected_color in category_colors.items():
            self.notification.category = category
            self.assertEqual(self.notification.category_color, expected_color)

    def test_type_color_mapping(self):
        type_colors = {
            'info': '#17a2b8',
            'success': '#28a745',
            'warning': '#ffc107',
            'error': '#dc3545',
        }
        for ntype, expected_color in type_colors.items():
            self.notification.notification_type = ntype
            self.assertEqual(self.notification.type_color, expected_color)


class NotificationPreferenceModelTests(TestCase):
    """Tests for the NotificationPreference model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='prefuser', password='test123', role='user'
        )
        self.prefs = NotificationPreference.objects.create(user=self.user)

    def test_default_values(self):
        self.assertTrue(self.prefs.notify_reservation)
        self.assertTrue(self.prefs.notify_payment)
        self.assertTrue(self.prefs.notify_system)
        self.assertFalse(self.prefs.notify_report)
        self.assertFalse(self.prefs.notify_promotion)
        self.assertTrue(self.prefs.in_app_notifications)
        self.assertFalse(self.prefs.email_notifications)
        self.assertEqual(self.prefs.frequency, 'instant')

    def test_str_representation(self):
        self.assertEqual(str(self.prefs), 'Preferences for prefuser')

    def test_is_category_enabled_all_enabled(self):
        self.assertTrue(self.prefs.is_category_enabled('reservation'))
        self.assertTrue(self.prefs.is_category_enabled('payment'))
        self.assertTrue(self.prefs.is_category_enabled('system'))

    def test_is_category_enabled_disabled(self):
        self.prefs.notify_report = False
        self.prefs.save()
        self.assertFalse(self.prefs.is_category_enabled('report'))

    def test_is_category_enabled_unknown_returns_true(self):
        """Unknown categories should default to enabled."""
        self.assertTrue(self.prefs.is_category_enabled('unknown_category'))


class BroadcastMessageModelTests(TestCase):
    """Tests for the BroadcastMessage model."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', password='test123', role='super_admin'
        )
        self.broadcast = BroadcastMessage.objects.create(
            title='Test Broadcast',
            message='This is a broadcast message.',
            sent_by=self.admin,
            status='draft',
        )

    def test_broadcast_creation(self):
        self.assertEqual(self.broadcast.title, 'Test Broadcast')
        self.assertEqual(self.broadcast.status, 'draft')
        self.assertEqual(self.broadcast.target_type, 'all')
        self.assertEqual(self.broadcast.priority, 'normal')

    def test_str_representation(self):
        self.assertEqual(str(self.broadcast), 'Broadcast: Test Broadcast')


class NotificationTemplateModelTests(TestCase):
    """Tests for the NotificationTemplate model."""

    def setUp(self):
        self.template = NotificationTemplate.objects.create(
            name='reservation_confirmed',
            title_template='Reservation Confirmed',
            message_template='Your reservation for {court_name} is confirmed!',
            category='reservation',
            notification_type='success',
            priority='normal',
        )

    def test_template_creation(self):
        self.assertEqual(self.template.name, 'reservation_confirmed')
        self.assertTrue(self.template.is_active)

    def test_render_title(self):
        result = self.template.render_title()
        self.assertEqual(result, 'Reservation Confirmed')

    def test_render_message(self):
        result = self.template.render_message(court_name='Court A')
        self.assertEqual(result, 'Your reservation for Court A is confirmed!')

    def test_str_representation(self):
        self.assertEqual(str(self.template), 'reservation_confirmed')


# ==================== VIEW TESTS (Regular User) ====================

class NotificationListViewTests(TestCase):
    """Tests for the notification list view."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='test123', role='user'
        )
        self.client.login(username='testuser', password='test123')

        # Create test notifications
        self.notif1 = Notification.objects.create(
            user=self.user, title='First', message='First notification',
            category='system', notification_type='info',
            created_at=timezone.now() - timedelta(hours=2),
        )
        self.notif2 = Notification.objects.create(
            user=self.user, title='Second', message='Second notification',
            category='reservation', notification_type='success',
            is_read=True,
            created_at=timezone.now() - timedelta(days=1),
        )
        self.notif3 = Notification.objects.create(
            user=self.user, title='Urgent', message='Urgent notification',
            category='payment', notification_type='error',
            priority='high',
            created_at=timezone.now() - timedelta(hours=1),
        )

        # Create notification for another user (should not appear)
        self.other_user = User.objects.create_user(
            username='other', password='test123', role='user'
        )
        Notification.objects.create(
            user=self.other_user, title='Other', message='Other notification',
        )

    def test_list_view_status_code(self):
        response = self.client.get(reverse('notification_list'))
        self.assertEqual(response.status_code, 200)

    def test_list_view_uses_correct_template(self):
        response = self.client.get(reverse('notification_list'))
        self.assertTemplateUsed(response, 'user/notifications/notification_list.html')

    def test_list_view_shows_only_user_notifications(self):
        response = self.client.get(reverse('notification_list'))
        self.assertContains(response, 'First')
        self.assertContains(response, 'Second')
        self.assertContains(response, 'Urgent')
        self.assertNotContains(response, 'Other')

    def test_list_view_stats_in_context(self):
        response = self.client.get(reverse('notification_list'))
        self.assertEqual(response.context['total_count'], 3)
        self.assertEqual(response.context['unread_count'], 2)  # notif1 unread, notif3 unread, notif2 read
        self.assertEqual(response.context['read_count'], 1)

    def test_list_view_search_by_title(self):
        response = self.client.get(reverse('notification_list'), {'search': 'Urgent'})
        self.assertContains(response, 'Urgent')
        self.assertNotContains(response, 'First')
        self.assertNotContains(response, 'Second')

    def test_list_view_search_by_message(self):
        response = self.client.get(reverse('notification_list'), {'search': 'Second notification'})
        self.assertContains(response, 'Second')
        self.assertNotContains(response, 'First')
        self.assertNotContains(response, 'Urgent')

    def test_list_view_search_no_results(self):
        response = self.client.get(reverse('notification_list'), {'search': 'Nonexistent'})
        self.assertNotContains(response, 'First')
        self.assertNotContains(response, 'Second')
        self.assertNotContains(response, 'Urgent')

    def test_list_view_filter_by_status_unread(self):
        response = self.client.get(reverse('notification_list'), {'status': 'unread'})
        self.assertContains(response, 'First')
        self.assertContains(response, 'Urgent')
        self.assertNotContains(response, 'Second')

    def test_list_view_filter_by_status_read(self):
        response = self.client.get(reverse('notification_list'), {'status': 'read'})
        self.assertContains(response, 'Second')
        self.assertNotContains(response, 'First')
        self.assertNotContains(response, 'Urgent')

    def test_list_view_filter_by_category(self):
        response = self.client.get(reverse('notification_list'), {'category': 'reservation'})
        self.assertContains(response, 'Second')
        self.assertNotContains(response, 'First')
        self.assertNotContains(response, 'Urgent')

    def test_list_view_filter_by_priority(self):
        response = self.client.get(reverse('notification_list'), {'priority': 'high'})
        self.assertContains(response, 'Urgent')
        self.assertNotContains(response, 'First')
        self.assertNotContains(response, 'Second')

    def test_list_view_filter_by_date_today(self):
        response = self.client.get(reverse('notification_list'), {'date': 'today'})
        self.assertContains(response, 'First')
        self.assertContains(response, 'Urgent')
        self.assertNotContains(response, 'Second')

    def test_list_view_filter_by_date_yesterday(self):
        response = self.client.get(reverse('notification_list'), {'date': 'yesterday'})
        self.assertContains(response, 'Second')
        self.assertNotContains(response, 'First')
        self.assertNotContains(response, 'Urgent')

    def test_list_view_filter_by_date_week(self):
        """Date filter for 'this week' should return all recent notifications."""
        response = self.client.get(reverse('notification_list'), {'date': 'week'})
        self.assertContains(response, 'First')
        self.assertContains(response, 'Second')  # Yesterday is within this week
        self.assertContains(response, 'Urgent')

    def test_list_view_filter_by_date_month(self):
        """Date filter for 'this month' should return all recent notifications."""
        response = self.client.get(reverse('notification_list'), {'date': 'month'})
        self.assertContains(response, 'First')
        self.assertContains(response, 'Second')
        self.assertContains(response, 'Urgent')

    def test_list_view_filter_by_type(self):
        """Type filter should filter by notification_type."""
        response = self.client.get(reverse('notification_list'), {'type': 'error'})
        self.assertContains(response, 'Urgent')
        self.assertNotContains(response, 'First')
        self.assertNotContains(response, 'Second')

    def test_list_view_sort_newest_first(self):
        response = self.client.get(reverse('notification_list'), {'sort': '-created_at'})
        # Order should be: Urgent (1h ago), First (2h ago), Second (1d ago)
        content = response.content.decode()
        self.assertLess(content.index('Urgent'), content.index('First'))
        self.assertLess(content.index('First'), content.index('Second'))

    def test_list_view_sort_oldest_first(self):
        response = self.client.get(reverse('notification_list'), {'sort': 'created_at'})
        content = response.content.decode()
        self.assertGreater(content.index('Urgent'), content.index('First'))

    def test_list_view_archive_filter(self):
        # Archive a notification
        self.notif1.archive()
        response = self.client.get(reverse('notification_list'), {'archive': 'archived'})
        self.assertContains(response, 'First')
        self.assertNotContains(response, 'Second')
        self.assertNotContains(response, 'Urgent')

    def test_list_view_pagination_context(self):
        response = self.client.get(reverse('notification_list'))
        self.assertIn('is_paginated', response.context)
        self.assertIn('page_obj', response.context)

    def test_list_view_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('notification_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_list_view_contains_modern_ui_elements(self):
        response = self.client.get(reverse('notification_list'))
        # Check for stat cards
        self.assertContains(response, 'Total')
        self.assertContains(response, 'Unread')
        self.assertContains(response, 'Read')
        self.assertContains(response, 'Today')
        # Check for filter elements
        self.assertContains(response, 'Search')
        self.assertContains(response, 'Status')
        self.assertContains(response, 'Category')
        self.assertContains(response, 'Priority')
        self.assertContains(response, 'Sort')
        # Check for action buttons
        self.assertContains(response, 'Mark All Read')
        self.assertContains(response, 'Delete Selected')
        self.assertContains(response, 'Clear All')
        self.assertContains(response, 'Reset')

    def test_list_view_grouped_by_time(self):
        response = self.client.get(reverse('notification_list'))
        self.assertContains(response, 'Today')
        self.assertContains(response, 'Yesterday')


class NotificationDetailViewTests(TestCase):
    """Tests for the notification detail view."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='test123', role='user'
        )
        self.client.login(username='testuser', password='test123')
        self.notification = Notification.objects.create(
            user=self.user,
            title='Detail Test',
            message='This is a detail test message.',
            category='payment',
            notification_type='success',
            priority='high',
            action_url='/user/payments/',
            action_text='View Payment',
        )

    def test_detail_view_status_code(self):
        response = self.client.get(
            reverse('notification_detail', args=[self.notification.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_detail_view_uses_correct_template(self):
        response = self.client.get(
            reverse('notification_detail', args=[self.notification.id])
        )
        self.assertTemplateUsed(response, 'user/notifications/notification_detail.html')

    def test_detail_view_shows_notification_data(self):
        response = self.client.get(
            reverse('notification_detail', args=[self.notification.id])
        )
        self.assertContains(response, 'Detail Test')
        self.assertContains(response, 'This is a detail test message.')
        self.assertContains(response, 'Payments')
        self.assertContains(response, 'High')

    def test_detail_view_marks_as_read(self):
        self.assertFalse(self.notification.is_read)
        response = self.client.get(
            reverse('notification_detail', args=[self.notification.id])
        )
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)
        self.assertIsNotNone(self.notification.read_at)

    def test_detail_view_404_for_wrong_user(self):
        other_user = User.objects.create_user(
            username='other', password='test123', role='user'
        )
        other_notification = Notification.objects.create(
            user=other_user, title='Other', message='Other message'
        )
        response = self.client.get(
            reverse('notification_detail', args=[other_notification.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_detail_view_404_nonexistent(self):
        response = self.client.get(
            reverse('notification_detail', args=[999])
        )
        self.assertEqual(response.status_code, 404)

    def test_detail_view_contains_action_button(self):
        response = self.client.get(
            reverse('notification_detail', args=[self.notification.id])
        )
        self.assertContains(response, 'View Payment')

    def test_detail_view_contains_modern_ui_elements(self):
        response = self.client.get(
            reverse('notification_detail', args=[self.notification.id])
        )
        self.assertContains(response, 'Received')
        self.assertContains(response, 'Status')
        self.assertContains(response, 'Priority')
        self.assertContains(response, 'Type')
        self.assertContains(response, 'Mark as Read')
        self.assertContains(response, 'Back to Notifications')

    def test_detail_view_empty_title_renders(self):
        """Notifications with empty title should render without error."""
        empty_title = Notification.objects.create(
            user=self.user,
            title='',
            message='This notification has no title',
        )
        response = self.client.get(
            reverse('notification_detail', args=[empty_title.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This notification has no title')


class MarkReadUnreadViewTests(TestCase):
    """Tests for marking notifications as read/unread."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='test123', role='user'
        )
        self.client.login(username='testuser', password='test123')
        self.notification = Notification.objects.create(
            user=self.user, title='Test', message='Test message'
        )

    def test_mark_as_read(self):
        response = self.client.get(
            reverse('mark_notification_read', args=[self.notification.id])
        )
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)
        self.assertIsNotNone(self.notification.read_at)

    def test_mark_as_read_redirects(self):
        response = self.client.get(
            reverse('mark_notification_read', args=[self.notification.id])
        )
        self.assertEqual(response.status_code, 302)

    def test_mark_as_unread(self):
        self.notification.mark_as_read()
        response = self.client.get(
            reverse('mark_notification_unread', args=[self.notification.id])
        )
        self.notification.refresh_from_db()
        self.assertFalse(self.notification.is_read)
        self.assertIsNone(self.notification.read_at)

    def test_mark_as_read_ajax(self):
        response = self.client.get(
            reverse('mark_notification_read', args=[self.notification.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': True})

    def test_mark_as_unread_ajax(self):
        self.notification.mark_as_read()
        response = self.client.get(
            reverse('mark_notification_unread', args=[self.notification.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': True})

    def test_mark_all_read(self):
        Notification.objects.create(user=self.user, title='N2', message='N2')
        Notification.objects.create(user=self.user, title='N3', message='N3')
        response = self.client.get(reverse('mark_all_read'))
        unread_count = Notification.objects.filter(
            user=self.user, is_read=False
        ).count()
        self.assertEqual(unread_count, 0)

    def test_mark_all_read_ajax(self):
        Notification.objects.create(user=self.user, title='N2', message='N2')
        response = self.client.get(
            reverse('mark_all_read'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': True, 'count': 2})


class DeleteNotificationViewTests(TestCase):
    """Tests for deleting notifications."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='test123', role='user'
        )
        self.client.login(username='testuser', password='test123')
        self.notification = Notification.objects.create(
            user=self.user, title='Delete Me', message='Delete this'
        )

    def test_delete_single(self):
        response = self.client.get(
            reverse('delete_notification', args=[self.notification.id])
        )
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_deleted)

    def test_delete_single_redirects(self):
        response = self.client.get(
            reverse('delete_notification', args=[self.notification.id])
        )
        self.assertEqual(response.status_code, 302)

    def test_delete_selected_post(self):
        n2 = Notification.objects.create(
            user=self.user, title='N2', message='N2'
        )
        n3 = Notification.objects.create(
            user=self.user, title='N3', message='N3'
        )
        response = self.client.post(
            reverse('delete_selected_notifications'),
            {'notification_ids': [n2.id, n3.id]}
        )
        n2.refresh_from_db()
        n3.refresh_from_db()
        self.assertTrue(n2.is_deleted)
        self.assertTrue(n3.is_deleted)

    def test_delete_selected_get_redirects(self):
        response = self.client.get(reverse('delete_selected_notifications'))
        self.assertEqual(response.status_code, 302)

    def test_clear_all(self):
        n2 = Notification.objects.create(
            user=self.user, title='N2', message='N2'
        )
        response = self.client.post(reverse('clear_all_notifications'))
        self.notification.refresh_from_db()
        n2.refresh_from_db()
        self.assertTrue(self.notification.is_deleted)
        self.assertTrue(n2.is_deleted)

    def test_clear_all_get_redirects(self):
        response = self.client.get(reverse('clear_all_notifications'))
        self.assertEqual(response.status_code, 302)

    def test_delete_other_user_notification_404(self):
        other_user = User.objects.create_user(
            username='other', password='test123', role='user'
        )
        other_notif = Notification.objects.create(
            user=other_user, title='Other', message='Other'
        )
        response = self.client.get(
            reverse('delete_notification', args=[other_notif.id])
        )
        self.assertEqual(response.status_code, 404)


class ArchiveRestoreViewTests(TestCase):
    """Tests for archiving and restoring notifications."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='test123', role='user'
        )
        self.client.login(username='testuser', password='test123')
        self.notification = Notification.objects.create(
            user=self.user, title='Archive Me', message='Archive this'
        )

    def test_archive(self):
        response = self.client.get(
            reverse('archive_notification', args=[self.notification.id])
        )
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_archived)
        self.assertIsNotNone(self.notification.archived_at)

    def test_restore(self):
        self.notification.archive()
        response = self.client.get(
            reverse('restore_notification', args=[self.notification.id])
        )
        self.notification.refresh_from_db()
        self.assertFalse(self.notification.is_archived)
        self.assertIsNone(self.notification.archived_at)

    def test_archive_redirects(self):
        response = self.client.get(
            reverse('archive_notification', args=[self.notification.id])
        )
        self.assertEqual(response.status_code, 302)

    def test_restore_redirects(self):
        self.notification.archive()
        response = self.client.get(
            reverse('restore_notification', args=[self.notification.id])
        )
        self.assertEqual(response.status_code, 302)


class NotificationPreferencesViewTests(TestCase):
    """Tests for the notification preferences view."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='prefuser', password='test123', role='user'
        )
        self.client.login(username='prefuser', password='test123')

    def test_preferences_get(self):
        response = self.client.get(reverse('notification_preferences'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/notifications/notification_preferences.html')

    def test_preferences_creates_prefs_on_first_access(self):
        self.assertFalse(
            NotificationPreference.objects.filter(user=self.user).exists()
        )
        response = self.client.get(reverse('notification_preferences'))
        self.assertTrue(
            NotificationPreference.objects.filter(user=self.user).exists()
        )

    def test_preferences_post_updates(self):
        prefs = NotificationPreference.objects.create(user=self.user)
        response = self.client.post(reverse('notification_preferences'), {
            'notify_reservation': 'on',
            'notify_payment': 'on',
            'notify_refund': 'on',
            'notify_cancellation': 'on',
            'notify_tournament': 'on',
            'notify_equipment': 'on',
            'notify_organization': 'on',
            'notify_staff': 'on',
            'notify_user': 'on',
            'notify_system': 'on',
            'notify_security': 'on',
            'notify_maintenance': 'on',
            'notify_announcement': 'on',
            'notify_message': 'on',
            'notify_account': 'on',
            'email_notifications': 'on',
            'push_notifications': 'on',
            'in_app_notifications': 'on',
            'frequency': 'daily',
            'quiet_hours_start': '22:00',
            'quiet_hours_end': '07:00',
        })
        prefs.refresh_from_db()
        self.assertTrue(prefs.notify_reservation)
        self.assertTrue(prefs.notify_payment)
        self.assertTrue(prefs.email_notifications)
        self.assertTrue(prefs.push_notifications)
        self.assertEqual(prefs.frequency, 'daily')
        self.assertIsNotNone(prefs.quiet_hours_start)
        self.assertIsNotNone(prefs.quiet_hours_end)

    def test_preferences_post_turn_off_all(self):
        prefs = NotificationPreference.objects.create(user=self.user)
        response = self.client.post(reverse('notification_preferences'), {
            'frequency': 'instant',
        })
        prefs.refresh_from_db()
        self.assertFalse(prefs.notify_reservation)
        self.assertFalse(prefs.notify_payment)
        self.assertFalse(prefs.email_notifications)
        self.assertFalse(prefs.push_notifications)

    def test_preferences_redirects_after_post(self):
        response = self.client.post(reverse('notification_preferences'), {
            'frequency': 'instant',
        })
        self.assertEqual(response.status_code, 302)

    def test_preferences_contains_modern_ui_elements(self):
        response = self.client.get(reverse('notification_preferences'))
        self.assertContains(response, 'Notification Preferences')
        self.assertContains(response, 'Notification Categories')
        self.assertContains(response, 'Delivery Methods')
        self.assertContains(response, 'Frequency')
        self.assertContains(response, 'Quiet Hours')
        self.assertContains(response, 'Save Preferences')


class UnreadCountAPITests(TestCase):
    """Tests for the unread count API endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='test123', role='user'
        )
        self.client.login(username='testuser', password='test123')
        Notification.objects.create(
            user=self.user, title='N1', message='N1', is_read=False
        )
        Notification.objects.create(
            user=self.user, title='N2', message='N2', is_read=False
        )
        Notification.objects.create(
            user=self.user, title='N3', message='N3', is_read=True
        )

    def test_unread_count_api(self):
        response = self.client.get(reverse('notification_unread_api'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['unread_count'], 2)

    def test_unread_count_api_includes_recent(self):
        response = self.client.get(reverse('notification_unread_api'))
        data = response.json()
        self.assertIn('recent', data)
        self.assertEqual(len(data['recent']), 3)

    def test_unread_count_api_recent_has_fields(self):
        response = self.client.get(reverse('notification_unread_api'))
        data = response.json()
        recent = data['recent'][0]
        self.assertIn('id', recent)
        self.assertIn('title', recent)
        self.assertIn('message', recent)
        self.assertIn('type', recent)
        self.assertIn('category', recent)
        self.assertIn('time', recent)
        self.assertIn('is_read', recent)
        self.assertIn('icon_class', recent)

    def test_unread_count_api_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('notification_unread_api'))
        self.assertEqual(response.status_code, 302)


# ==================== ROLE-BASED ACCESS TESTS ====================

class NotificationRoleBasedAccessTests(TestCase):
    """Tests that notification views are accessible by appropriate roles."""

    def setUp(self):
        self.super_admin = User.objects.create_user(
            username='sa', password='test123', role='super_admin'
        )
        self.org_admin = User.objects.create_user(
            username='oa', password='test123', role='org_admin'
        )
        self.org_staff = User.objects.create_user(
            username='os', password='test123', role='org_staff'
        )
        self.regular_user = User.objects.create_user(
            username='user', password='test123', role='user'
        )

    def test_notification_list_all_roles(self):
        for username in ['sa', 'oa', 'os', 'user']:
            self.client.login(username=username, password='test123')
            response = self.client.get(reverse('notification_list'))
            self.assertEqual(response.status_code, 200,
                             f'{username} should access notification list')

    def test_unauthenticated_redirected_to_login(self):
        response = self.client.get(reverse('notification_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_all_views_require_login(self):
        """All notification views should redirect unauthenticated users."""
        self.client.logout()
        # Create a notification owned by nobody for URL lookups
        temp_user = User.objects.create_user(
            username='temp', password='test123', role='user'
        )
        notif = Notification.objects.create(
            user=temp_user, title='Temp', message='Temp'
        )
        view_urls = [
            reverse('notification_detail', args=[notif.id]),
            reverse('mark_notification_read', args=[notif.id]),
            reverse('mark_notification_unread', args=[notif.id]),
            reverse('mark_all_read'),
            reverse('delete_notification', args=[notif.id]),
            reverse('archive_notification', args=[notif.id]),
            reverse('restore_notification', args=[notif.id]),
            reverse('notification_preferences'),
        ]
        for url in view_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302,
                             f'{url} should require login')
            self.assertIn('login', response.url,
                          f'{url} should redirect to login')


# ==================== UTILITY FUNCTION TESTS ====================

class NotificationUtilityTests(TestCase):
    """Tests for notification utility functions."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='test123', role='user'
        )

    def test_create_notification_via_model(self):
        notification = Notification.objects.create(
            user=self.user,
            title='Test Title',
            message='Test Message',
            notification_type='success',
            category='payment',
            priority='high',
            action_url='/test/',
            action_text='View Test',
        )
        self.assertEqual(notification.title, 'Test Title')
        self.assertEqual(notification.action_text, 'View Test')
        self.assertEqual(notification.priority, 'high')


# ==================== EMPTY STATE TESTS ====================

class NotificationEmptyStateTests(TestCase):
    """Tests for empty states in notification views."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='test123', role='user'
        )
        self.client.login(username='testuser', password='test123')

    def test_empty_list_shows_all_caught_up(self):
        response = self.client.get(reverse('notification_list'))
        self.assertContains(response, 'All caught up')

    def test_empty_list_shows_no_notifications_message(self):
        response = self.client.get(reverse('notification_list'))
        self.assertContains(response, 'no notifications')
        self.assertContains(response, 'bell-slash')

    def test_empty_search_shows_no_matching(self):
        response = self.client.get(reverse('notification_list'), {'search': 'nothing'})
        self.assertContains(response, 'No matching notifications')

    def test_empty_archive_shows_no_archived(self):
        response = self.client.get(reverse('notification_list'), {'archive': 'archived'})
        self.assertContains(response, 'No archived notifications')

    def test_empty_list_shows_category_badges(self):
        """Empty state should show category hints."""
        response = self.client.get(reverse('notification_list'))
        self.assertContains(response, 'Reservations')
        self.assertContains(response, 'Payments')
        self.assertContains(response, 'Tournaments')


# ==================== NOTIFICATION WITH RELATED OBJECTS ====================

class NotificationRelatedObjectsTests(TestCase):
    """Tests for notifications with related objects."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='test123', role='user'
        )
        self.client.login(username='testuser', password='test123')

    def test_detail_without_related_objects(self):
        """Notification detail should not show Related Information section."""
        notification = Notification.objects.create(
            user=self.user,
            title='No Related',
            message='No related objects',
        )
        response = self.client.get(
            reverse('notification_detail', args=[notification.id])
        )
        # Should show the notification, nothing more is needed
        self.assertContains(response, 'No Related')
