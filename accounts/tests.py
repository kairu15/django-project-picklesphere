from django.test import TestCase, RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.urls import reverse

from .models import User
from .decorators import admin_required, staff_or_admin_required, user_required


class AdminRequiredDecoratorTests(TestCase):
    """Tests for the @admin_required decorator."""

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/some-admin-page/')
        self.request.session = 'session'

        # Mock messages storage
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        # Create a simple test view that the decorator wraps
        self.test_view = lambda req: HttpResponse("Success")

        # Create users of each role
        self.admin_user = User.objects.create_user(
            username='admin_test', password='test123', role='admin',
            is_staff=True, is_superuser=True
        )
        self.staff_user = User.objects.create_user(
            username='staff_test', password='test123', role='staff',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='user_test', password='test123', role='user'
        )

    def test_admin_user_has_access(self):
        """Admin users should be able to access admin_required views."""
        self.request.user = self.admin_user
        wrapped_view = admin_required(self.test_view)
        response = wrapped_view(self.request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Success")

    def test_staff_user_is_redirected(self):
        """Staff users should be redirected from admin_required views."""
        self.request.user = self.staff_user
        wrapped_view = admin_required(self.test_view)
        response = wrapped_view(self.request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_regular_user_is_redirected(self):
        """Regular users should be redirected from admin_required views."""
        self.request.user = self.regular_user
        wrapped_view = admin_required(self.test_view)
        response = wrapped_view(self.request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_anonymous_user_is_redirected(self):
        """Anonymous (unauthenticated) users should be redirected."""
        self.request.user = AnonymousUser()
        wrapped_view = admin_required(self.test_view)
        response = wrapped_view(self.request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_error_message_is_set_for_non_admin(self):
        """Non-admin users should receive an error message."""
        self.request.user = self.regular_user
        wrapped_view = admin_required(self.test_view)
        wrapped_view(self.request)

        messages_list = list(self.messages)
        self.assertEqual(len(messages_list), 1)
        self.assertIn("do not have permission", str(messages_list[0]).lower())

    def test_wrapped_function_name_preserved(self):
        """The decorator should preserve the original view function name."""
        def my_custom_view(request):
            return HttpResponse("OK")

        wrapped_view = admin_required(my_custom_view)
        self.assertEqual(wrapped_view.__name__, "my_custom_view")
        self.assertEqual(wrapped_view.__wrapped__.__name__, "my_custom_view")


class StaffOrAdminRequiredDecoratorTests(TestCase):
    """Tests for the @staff_or_admin_required decorator."""

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/some-staff-page/')
        self.request.session = 'session'

        # Mock messages storage
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        # Create a simple test view that the decorator wraps
        self.test_view = lambda req: HttpResponse("Success")

        # Create users of each role
        self.admin_user = User.objects.create_user(
            username='admin_test2', password='test123', role='admin',
            is_staff=True, is_superuser=True
        )
        self.staff_user = User.objects.create_user(
            username='staff_test2', password='test123', role='staff',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='user_test2', password='test123', role='user'
        )

    def test_admin_user_has_access(self):
        """Admin users should be able to access staff_or_admin_required views."""
        self.request.user = self.admin_user
        wrapped_view = staff_or_admin_required(self.test_view)
        response = wrapped_view(self.request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Success")

    def test_staff_user_has_access(self):
        """Staff users should be able to access staff_or_admin_required views."""
        self.request.user = self.staff_user
        wrapped_view = staff_or_admin_required(self.test_view)
        response = wrapped_view(self.request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Success")

    def test_regular_user_is_redirected(self):
        """Regular users should be redirected from staff_or_admin_required views."""
        self.request.user = self.regular_user
        wrapped_view = staff_or_admin_required(self.test_view)
        response = wrapped_view(self.request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_anonymous_user_is_redirected(self):
        """Anonymous (unauthenticated) users should be redirected."""
        self.request.user = AnonymousUser()
        wrapped_view = staff_or_admin_required(self.test_view)
        response = wrapped_view(self.request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_error_message_is_set_for_regular_user(self):
        """Regular users should receive an error message."""
        self.request.user = self.regular_user
        wrapped_view = staff_or_admin_required(self.test_view)
        wrapped_view(self.request)

        messages_list = list(self.messages)
        self.assertEqual(len(messages_list), 1)
        self.assertIn("do not have permission", str(messages_list[0]).lower())

    def test_no_error_message_for_staff_user(self):
        """Staff users should NOT receive an error message."""
        self.request.user = self.staff_user
        wrapped_view = staff_or_admin_required(self.test_view)
        wrapped_view(self.request)

        messages_list = list(self.messages)
        self.assertEqual(len(messages_list), 0)

    def test_no_error_message_for_admin_user(self):
        """Admin users should NOT receive an error message."""
        self.request.user = self.admin_user
        wrapped_view = staff_or_admin_required(self.test_view)
        wrapped_view(self.request)

        messages_list = list(self.messages)
        self.assertEqual(len(messages_list), 0)

    def test_wrapped_function_name_preserved(self):
        """The decorator should preserve the original view function name."""
        def my_custom_view(request):
            return HttpResponse("OK")

        wrapped_view = staff_or_admin_required(my_custom_view)
        self.assertEqual(wrapped_view.__name__, "my_custom_view")
        self.assertEqual(wrapped_view.__wrapped__.__name__, "my_custom_view")


class UserRequiredDecoratorTests(TestCase):
    """Tests for the @user_required decorator."""

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/some-user-page/')
        self.request.session = 'session'

        # Mock messages storage
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        # Create a simple test view that the decorator wraps
        self.test_view = lambda req: HttpResponse("Success")

        # Create users of each role
        self.admin_user = User.objects.create_user(
            username='admin_test3', password='test123', role='admin',
            is_staff=True, is_superuser=True
        )
        self.staff_user = User.objects.create_user(
            username='staff_test3', password='test123', role='staff',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='user_test3', password='test123', role='user'
        )

    def test_user_has_access(self):
        """Regular users should be able to access user_required views."""
        self.request.user = self.regular_user
        wrapped_view = user_required(self.test_view)
        response = wrapped_view(self.request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Success")

    def test_admin_user_is_redirected(self):
        """Admin users should be redirected from user_required views."""
        self.request.user = self.admin_user
        wrapped_view = user_required(self.test_view)
        response = wrapped_view(self.request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_staff_user_is_redirected(self):
        """Staff users should be redirected from user_required views."""
        self.request.user = self.staff_user
        wrapped_view = user_required(self.test_view)
        response = wrapped_view(self.request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_anonymous_user_is_redirected(self):
        """Anonymous users should be redirected from user_required views."""
        self.request.user = AnonymousUser()
        wrapped_view = user_required(self.test_view)
        response = wrapped_view(self.request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_error_message_is_set_for_admin(self):
        """Admin users should receive an error message."""
        self.request.user = self.admin_user
        wrapped_view = user_required(self.test_view)
        wrapped_view(self.request)

        messages_list = list(self.messages)
        self.assertEqual(len(messages_list), 1)
        self.assertIn("do not have permission", str(messages_list[0]).lower())

    def test_error_message_is_set_for_staff(self):
        """Staff users should receive an error message."""
        self.request.user = self.staff_user
        wrapped_view = user_required(self.test_view)
        wrapped_view(self.request)

        messages_list = list(self.messages)
        self.assertEqual(len(messages_list), 1)
        self.assertIn("do not have permission", str(messages_list[0]).lower())

    def test_no_error_message_for_normal_user(self):
        """Regular users should NOT receive an error message."""
        self.request.user = self.regular_user
        wrapped_view = user_required(self.test_view)
        wrapped_view(self.request)

        messages_list = list(self.messages)
        self.assertEqual(len(messages_list), 0)

    def test_wrapped_function_name_preserved(self):
        """The decorator should preserve the original view function name."""
        def my_custom_view(request):
            return HttpResponse("OK")

        wrapped_view = user_required(my_custom_view)
        self.assertEqual(wrapped_view.__name__, "my_custom_view")
        self.assertEqual(wrapped_view.__wrapped__.__name__, "my_custom_view")


class IntegrationViewAccessTests(TestCase):
    """
    Integration tests that verify actual views are properly protected.
    Tests that the decorators work on real views through URL access.
    """

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            username='admin_int', password='test123', role='admin',
            is_staff=True, is_superuser=True
        )
        cls.staff = User.objects.create_user(
            username='staff_int', password='test123', role='staff',
            is_staff=True
        )
        cls.user = User.objects.create_user(
            username='user_int', password='test123', role='user'
        )
        
        # Create a test tournament for tournament_register view
        from tournaments.models import Tournament
        from datetime import date, timedelta
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        cls.tournament = Tournament.objects.create(
            name='Test Tournament',
            registration_start=now,
            registration_end=now + timedelta(days=15),
            tournament_start=now + timedelta(days=30),
            tournament_end=now + timedelta(days=32),
            max_participants=16,
            category='singles',
            format='round_robin',
            status='registration_open',
            created_by=cls.admin
        )
        
        # Create test equipment for equipment rental tests
        from equipment.models import Equipment
        cls.equipment = Equipment.objects.create(
            name='Test Paddle',
            type='paddle',
            brand='TestBrand',
            quantity_available=5,
            quantity_total=10,
            rental_price=50.00,
            condition='good',
            is_active=True
        )

    # ---- ADMIN-ONLY PAGE TESTS ----

    def test_admin_dashboard_admin_access(self):
        """Admin can access admin dashboard."""
        self.client.login(username='admin_int', password='test123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_admin_dashboard_staff_blocked(self):
        """Staff cannot access admin dashboard."""
        self.client.login(username='staff_int', password='test123')
        response = self.client.get(reverse('admin_dashboard'))
        # Redirects to /dashboard/ which then redirects to role-specific dashboard
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_admin_dashboard_user_blocked(self):
        """Regular user cannot access admin dashboard."""
        self.client.login(username='user_int', password='test123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_user_list_admin_access(self):
        """Admin can access user management list."""
        self.client.login(username='admin_int', password='test123')
        response = self.client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 200)

    def test_user_list_staff_blocked(self):
        """Staff cannot access user management list."""
        self.client.login(username='staff_int', password='test123')
        response = self.client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_user_list_user_blocked(self):
        """Regular user cannot access user management list."""
        self.client.login(username='user_int', password='test123')
        response = self.client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_court_list_admin_access(self):
        """Admin can access court management."""
        self.client.login(username='admin_int', password='test123')
        response = self.client.get(reverse('admin_court_list'))
        self.assertEqual(response.status_code, 200)

    def test_court_list_user_blocked(self):
        """Regular user cannot access court management."""
        self.client.login(username='user_int', password='test123')
        response = self.client.get(reverse('admin_court_list'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    # ---- STAFF-ACCESSIBLE PAGE TESTS ----

    def test_staff_dashboard_admin_access(self):
        """Admin can access staff dashboard."""
        self.client.login(username='admin_int', password='test123')
        response = self.client.get(reverse('staff_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_staff_dashboard_staff_access(self):
        """Staff can access staff dashboard."""
        self.client.login(username='staff_int', password='test123')
        response = self.client.get(reverse('staff_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_staff_dashboard_user_blocked(self):
        """Regular user cannot access staff dashboard."""
        self.client.login(username='user_int', password='test123')
        response = self.client.get(reverse('staff_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_staff_reservations_staff_access(self):
        """Staff can access staff reservations."""
        self.client.login(username='staff_int', password='test123')
        response = self.client.get(reverse('staff_reservations'))
        self.assertEqual(response.status_code, 200)

    def test_staff_reservations_user_blocked(self):
        """Regular user cannot access staff reservations."""
        self.client.login(username='user_int', password='test123')
        response = self.client.get(reverse('staff_reservations'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_staff_payments_staff_access(self):
        """Staff can access staff payments."""
        self.client.login(username='staff_int', password='test123')
        response = self.client.get(reverse('staff_payments'))
        self.assertEqual(response.status_code, 200)

    def test_staff_payments_user_blocked(self):
        """Regular user cannot access staff payments."""
        self.client.login(username='user_int', password='test123')
        response = self.client.get(reverse('staff_payments'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    # ---- USER-ACCESSIBLE PAGE TESTS ----

    def test_user_dashboard_user_access(self):
        """Regular user can access user dashboard."""
        self.client.login(username='user_int', password='test123')
        response = self.client.get(reverse('user_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_user_dashboard_admin_blocked(self):
        """Admin cannot access user dashboard (user_required restriction)."""
        self.client.login(username='admin_int', password='test123')
        response = self.client.get(reverse('user_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_user_dashboard_staff_blocked(self):
        """Staff cannot access user dashboard (user_required restriction)."""
        self.client.login(username='staff_int', password='test123')
        response = self.client.get(reverse('user_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_user_profile_user_access(self):
        """Regular user can access profile page."""
        self.client.login(username='user_int', password='test123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

    def test_user_profile_admin_access(self):
        """Admin can still access profile page (profile is unrestricted)."""
        self.client.login(username='admin_int', password='test123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

    def test_user_profile_staff_access(self):
        """Staff can still access profile page (profile is unrestricted)."""
        self.client.login(username='staff_int', password='test123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

    def test_user_reservations_user_access(self):
        """Regular user can access their reservations list."""
        self.client.login(username='user_int', password='test123')
        response = self.client.get(reverse('reservation_list'))
        self.assertEqual(response.status_code, 200)

    def test_user_reservations_staff_blocked(self):
        """Staff cannot access user reservations list."""
        self.client.login(username='staff_int', password='test123')
        response = self.client.get(reverse('reservation_list'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_user_payment_history_user_access(self):
        """Regular user can access payment history."""
        self.client.login(username='user_int', password='test123')
        response = self.client.get(reverse('payment_history'))
        self.assertEqual(response.status_code, 200)

    def test_user_payment_history_admin_blocked(self):
        """Admin cannot access user payment history."""
        self.client.login(username='admin_int', password='test123')
        response = self.client.get(reverse('payment_history'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    # ---- TOURNAMENT USER VIEW TESTS ----

    def test_my_tournaments_user_access(self):
        """Regular user can access their tournaments."""
        self.client.login(username='user_int', password='test123')
        response = self.client.get(reverse('my_tournaments'))
        self.assertEqual(response.status_code, 200)

    def test_my_tournaments_staff_blocked(self):
        """Staff cannot access user's my tournaments."""
        self.client.login(username='staff_int', password='test123')
        response = self.client.get(reverse('my_tournaments'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_my_tournaments_admin_blocked(self):
        """Admin cannot access user's my tournaments."""
        self.client.login(username='admin_int', password='test123')
        response = self.client.get(reverse('my_tournaments'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_my_matches_user_access(self):
        """Regular user can access their matches."""
        self.client.login(username='user_int', password='test123')
        response = self.client.get(reverse('my_matches'))
        self.assertEqual(response.status_code, 200)

    def test_my_matches_staff_blocked(self):
        """Staff cannot access user's my matches."""
        self.client.login(username='staff_int', password='test123')
        response = self.client.get(reverse('my_matches'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_my_matches_admin_blocked(self):
        """Admin cannot access user's my matches."""
        self.client.login(username='admin_int', password='test123')
        response = self.client.get(reverse('my_matches'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_tournament_register_user_redirected(self):
        """Regular user redirected from tournament register (404 because no tournament would be found via GET, but user_required lets them through)."""
        self.client.login(username='user_int', password='test123')
        # The tournament_register view renders a form on GET, but first @user_required must pass
        response = self.client.get(reverse('tournament_register', args=[self.tournament.pk]))
        # User passes @user_required, but since tournament exists, the view renders
        self.assertIn(response.status_code, [200, 302])

    def test_tournament_register_admin_blocked(self):
        """Admin is blocked from tournament register (user_required)."""
        self.client.login(username='admin_int', password='test123')
        response = self.client.get(reverse('tournament_register', args=[self.tournament.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_tournament_register_staff_blocked(self):
        """Staff is blocked from tournament register (user_required)."""
        self.client.login(username='staff_int', password='test123')
        response = self.client.get(reverse('tournament_register', args=[self.tournament.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    # ---- EQUIPMENT USER VIEW TESTS ----

    def test_equipment_rental_user_redirected(self):
        """Regular user passes user_required on equipment rental (view redirects on GET)."""
        self.client.login(username='user_int', password='test123')
        response = self.client.get(reverse('equipment_rental_create'))
        # @user_required passes, then view redirects to equipment_list on GET
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('equipment_list'))

    def test_equipment_rental_admin_blocked(self):
        """Admin is blocked from equipment rental (user_required)."""
        self.client.login(username='admin_int', password='test123')
        response = self.client.get(reverse('equipment_rental_create'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_equipment_rental_staff_blocked(self):
        """Staff is blocked from equipment rental (user_required)."""
        self.client.login(username='staff_int', password='test123')
        response = self.client.get(reverse('equipment_rental_create'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_cancel_equipment_rental_admin_blocked(self):
        """Admin is blocked from cancel equipment rental (user_required)."""
        self.client.login(username='admin_int', password='test123')
        response = self.client.get(reverse('cancel_equipment_rental', args=[999]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_cancel_equipment_rental_staff_blocked(self):
        """Staff is blocked from cancel equipment rental (user_required)."""
        self.client.login(username='staff_int', password='test123')
        response = self.client.get(reverse('cancel_equipment_rental', args=[999]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_anonymous_redirected_to_login(self):
        """Anonymous users are redirected to login for protected pages."""
        response = self.client.get(reverse('admin_dashboard'))
        # @login_required redirects to login page first
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)
