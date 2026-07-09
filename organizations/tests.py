from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta

from .models import Organization
from .forms import OrganizationRegistrationForm, OrganizationApprovalForm, OrganizationProfileForm, SuperAdminOrganizationForm
from accounts.models import User
from accounts.decorators import super_admin_required, org_admin_required, org_required
from courts.models import Court, Site
from tournaments.models import Tournament
from equipment.models import Equipment
from reservations.models import Reservation
from payments.models import Payment


# ==================== MODEL TESTS ====================

class OrganizationModelTests(TestCase):
    """Tests for the Organization model."""

    def setUp(self):
        self.org = Organization.objects.create(
            name='Test Pickleball Club',
            description='A great place to play',
            city='Makati',
            province='Metro Manila',
            contact_email='test@club.com',
            contact_phone='09170000000',
            status='pending'
        )

    def test_organization_creation(self):
        self.assertEqual(self.org.name, 'Test Pickleball Club')
        self.assertEqual(self.org.status, 'pending')
        self.assertTrue(self.org.is_active)
        self.assertEqual(self.org.max_staff_accounts, 5)

    def test_slug_auto_generated(self):
        self.assertEqual(self.org.slug, 'test-pickleball-club')

    def test_slug_uniqueness(self):
        """Test that slugs are unique even when names produce the same slug."""
        org2 = Organization.objects.create(name='test-pickleball-club')
        self.assertNotEqual(org2.slug, self.org.slug)
        self.assertTrue(org2.slug.startswith('test-pickleball-club'))

    def test_duplicate_name_raises(self):
        with self.assertRaises(Exception):
            Organization.objects.create(name='Test Pickleball Club')

    def test_str_representation(self):
        self.assertEqual(str(self.org), 'Test Pickleball Club')

    def test_court_count_property(self):
        site = Site.objects.create(name='Main', organization=self.org)
        Court.objects.create(name='Court 1', site=site, organization=self.org, is_active=True)
        Court.objects.create(name='Court 2', site=site, organization=self.org, is_active=True)
        Court.objects.create(name='Inactive Court', site=site, organization=self.org, is_active=False)
        self.assertEqual(self.org.court_count, 2)

    def test_staff_count_property(self):
        User.objects.create_user(username='staff1', password='test123', role='org_staff', organization=self.org)
        User.objects.create_user(username='staff2', password='test123', role='org_staff', organization=self.org)
        User.objects.create_user(username='admin1', password='test123', role='org_admin', organization=self.org)
        # Only counts org_staff, not org_admin
        self.assertEqual(self.org.staff_count, 2)

    def test_can_add_staff_within_limit(self):
        self.assertTrue(self.org.can_add_staff())
        # Fill up staff slots
        for i in range(self.org.max_staff_accounts):
            User.objects.create_user(
                username=f'staff{i}', password='test123',
                role='org_staff', organization=self.org
            )
        self.assertFalse(self.org.can_add_staff())

    def test_tournament_count_property(self):
        Tournament.objects.create(
            name='T1', organization=self.org,
            category='singles', format='round_robin',
            registration_start=timezone.now(),
            registration_end=timezone.now() + timedelta(days=10),
            tournament_start=timezone.now() + timedelta(days=20),
            tournament_end=timezone.now() + timedelta(days=22),
            status='draft', created_by=None
        )
        self.assertEqual(self.org.tournament_count, 1)


class OrganizationStatusTests(TestCase):
    """Tests for organization status workflow."""

    def setUp(self):
        self.super_admin = User.objects.create_user(
            username='sa', password='test123', role='super_admin'
        )
        self.org = Organization.objects.create(
            name='New Club', status='pending', registration_notes='We want to join!'
        )

    def test_initial_status_is_pending(self):
        self.assertEqual(self.org.status, 'pending')

    def test_approve_organization(self):
        self.org.status = 'approved'
        self.org.approved_by = self.super_admin
        self.org.approved_at = timezone.now()
        self.org.save()
        
        self.org.refresh_from_db()
        self.assertEqual(self.org.status, 'approved')
        self.assertEqual(self.org.approved_by, self.super_admin)
        self.assertIsNotNone(self.org.approved_at)

    def test_reject_organization(self):
        self.org.status = 'rejected'
        self.org.rejection_reason = 'Incomplete information'
        self.org.save()
        
        self.org.refresh_from_db()
        self.assertEqual(self.org.status, 'rejected')
        self.assertEqual(self.org.rejection_reason, 'Incomplete information')

    def test_suspend_organization(self):
        self.org.status = 'approved'
        self.org.save()
        
        self.org.status = 'suspended'
        self.org.save()
        
        self.org.refresh_from_db()
        self.assertEqual(self.org.status, 'suspended')

    def test_approve_reject_cycle(self):
        """Test approving then rejecting and re-approving."""
        self.org.status = 'approved'
        self.org.approved_by = self.super_admin
        self.org.approved_at = timezone.now()
        self.org.save()
        
        self.org.status = 'rejected'
        self.org.rejection_reason = 'Policy violation'
        self.org.save()
        
        self.org.status = 'approved'
        self.org.approved_at = timezone.now()
        self.org.rejection_reason = ''
        self.org.save()
        
        self.org.refresh_from_db()
        self.assertEqual(self.org.status, 'approved')
        self.assertEqual(self.org.rejection_reason, '')


# ==================== FORM TESTS ====================

class OrganizationFormTests(TestCase):
    """Tests for organization forms."""

    def test_registration_form_valid(self):
        form_data = {
            'name': 'New Organization',
            'contact_email': 'org@email.com',
            'registration_notes': 'We love pickleball!',
            'agree_terms': True,
        }
        form = OrganizationRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_registration_form_missing_name(self):
        form_data = {
            'contact_email': 'org@email.com',
            'agree_terms': True,
        }
        form = OrganizationRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_registration_form_missing_terms(self):
        form_data = {
            'name': 'New Org',
            'contact_email': 'org@email.com',
        }
        form = OrganizationRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('agree_terms', form.errors)

    def test_approval_form_valid(self):
        form_data = {
            'status': 'approved',
            'max_staff_accounts': 10,
        }
        form = OrganizationApprovalForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_profile_form_valid(self):
        form_data = {
            'name': 'Updated Club Name',
            'description': 'Updated description',
            'city': 'Cebu City',
            'province': 'Cebu',
        }
        form = OrganizationProfileForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)


# ==================== APPROVAL WORKFLOW INTEGRATION TESTS ====================

class OrganizationApprovalWorkflowTests(TestCase):
    """End-to-end tests for the organization approval workflow."""

    def setUp(self):
        self.super_admin = User.objects.create_user(
            username='sa', password='test123', role='super_admin'
        )
        self.regular_user = User.objects.create_user(
            username='user', password='test123', role='user'
        )

    def test_full_approval_workflow(self):
        """Register → approve → verify."""
        # 1. Register (public)
        response = self.client.post(reverse('organization_register'), {
            'name': 'Brand New Club',
            'contact_email': 'club@email.com',
            'registration_notes': 'We want to be part of PickleSphere!',
            'agree_terms': True,
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        org = Organization.objects.get(name='Brand New Club')
        self.assertEqual(org.status, 'pending')
        
        # 2. Login as super admin and approve
        self.client.login(username='sa', password='test123')
        response = self.client.post(
            reverse('super_admin_approve_organization', args=[org.pk]),
            {'status': 'approved', 'max_staff_accounts': 5}
        )
        self.assertEqual(response.status_code, 302)
        
        org.refresh_from_db()
        self.assertEqual(org.status, 'approved')
        self.assertEqual(org.approved_by, self.super_admin)
        self.assertIsNotNone(org.approved_at)

    def test_rejection_workflow(self):
        """Register → reject with reason."""
        self.client.post(reverse('organization_register'), {
            'name': 'Rejected Club',
            'contact_email': 'rejected@email.com',
            'registration_notes': 'Test',
            'agree_terms': True,
        })
        
        org = Organization.objects.get(name='Rejected Club')
        
        self.client.login(username='sa', password='test123')
        response = self.client.post(
            reverse('super_admin_approve_organization', args=[org.pk]),
            {'status': 'rejected', 'rejection_reason': 'Incomplete application', 'max_staff_accounts': 5}
        )
        self.assertEqual(response.status_code, 302)
        
        org.refresh_from_db()
        self.assertEqual(org.status, 'rejected')
        self.assertEqual(org.rejection_reason, 'Incomplete application')

    def test_regular_user_cannot_approve(self):
        """Regular users should not be able to access the approve view."""
        org = Organization.objects.create(name='Test Org', status='pending')
        
        self.client.login(username='user', password='test123')
        response = self.client.get(
            reverse('super_admin_approve_organization', args=[org.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('dashboard'), response.url)


# ==================== ORG-SCOPED COURT VIEW TESTS ====================

class OrgScopedCourtViewTests(TestCase):
    """Tests that org_admin users only see/ manage their own organization's courts."""

    def setUp(self):
        self.org1 = Organization.objects.create(name='Org 1', status='approved')
        self.org2 = Organization.objects.create(name='Org 2', status='approved')
        
        self.site1 = Site.objects.create(name='Site 1', organization=self.org1)
        self.site2 = Site.objects.create(name='Site 2', organization=self.org2)
        
        self.court1 = Court.objects.create(
            name='Court A', site=self.site1, organization=self.org1,
            hourly_rate=100, is_active=True
        )
        self.court2 = Court.objects.create(
            name='Court B', site=self.site2, organization=self.org2,
            hourly_rate=200, is_active=True
        )
        
        self.super_admin = User.objects.create_user(
            username='sa', password='test123', role='super_admin'
        )
        self.org1_admin = User.objects.create_user(
            username='oa1', password='test123', role='org_admin',
            organization=self.org1
        )
        self.org2_admin = User.objects.create_user(
            username='oa2', password='test123', role='org_admin',
            organization=self.org2
        )

    def test_super_admin_sees_all_courts(self):
        self.client.login(username='sa', password='test123')
        response = self.client.get(reverse('org_admin_court_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Court A')
        self.assertContains(response, 'Court B')

    def test_org1_admin_only_sees_own_courts(self):
        self.client.login(username='oa1', password='test123')
        response = self.client.get(reverse('org_admin_court_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Court A')
        self.assertNotContains(response, 'Court B')

    def test_org2_admin_only_sees_own_courts(self):
        self.client.login(username='oa2', password='test123')
        response = self.client.get(reverse('org_admin_court_list'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Court A')
        self.assertContains(response, 'Court B')

    def test_org_admin_cannot_edit_other_org_court(self):
        self.client.login(username='oa1', password='test123')
        # Trying to edit court2 (belongs to org2) should 404
        response = self.client.get(reverse('org_admin_court_edit', args=[self.court2.pk]))
        self.assertEqual(response.status_code, 404)

    def test_org_admin_can_edit_own_court(self):
        self.client.login(username='oa1', password='test123')
        response = self.client.get(reverse('org_admin_court_edit', args=[self.court1.pk]))
        self.assertEqual(response.status_code, 200)

    def test_org_admin_cannot_delete_other_org_court(self):
        self.client.login(username='oa1', password='test123')
        # POST to delete court2
        response = self.client.post(reverse('org_admin_court_delete', args=[self.court2.pk]))
        self.assertEqual(response.status_code, 404)

    def test_super_admin_can_delete_any_court(self):
        self.client.login(username='sa', password='test123')
        response = self.client.post(reverse('org_admin_court_delete', args=[self.court2.pk]))
        # Should succeed (redirect after deactivation)
        self.assertEqual(response.status_code, 302)
        self.court2.refresh_from_db()
        self.assertFalse(self.court2.is_active)


# ==================== ORG-SCOPED TOURNAMENT VIEW TESTS ====================

class OrgScopedTournamentViewTests(TestCase):
    """Tests that org_admin users only see/manage their own organization's tournaments."""

    def setUp(self):
        self.org1 = Organization.objects.create(name='Org 1', status='approved')
        self.org2 = Organization.objects.create(name='Org 2', status='approved')
        
        self.t1 = Tournament.objects.create(
            name='Tournament 1', organization=self.org1,
            category='singles', format='round_robin',
            registration_start=timezone.now(),
            registration_end=timezone.now() + timedelta(days=10),
            tournament_start=timezone.now() + timedelta(days=20),
            tournament_end=timezone.now() + timedelta(days=22),
            status='draft'
        )
        self.t2 = Tournament.objects.create(
            name='Tournament 2', organization=self.org2,
            category='doubles', format='single_elimination',
            registration_start=timezone.now(),
            registration_end=timezone.now() + timedelta(days=10),
            tournament_start=timezone.now() + timedelta(days=20),
            tournament_end=timezone.now() + timedelta(days=22),
            status='registration_open'
        )
        
        self.org1_admin = User.objects.create_user(
            username='oa1', password='test123', role='org_admin',
            organization=self.org1
        )

    def test_org_admin_only_sees_own_tournaments(self):
        self.client.login(username='oa1', password='test123')
        response = self.client.get(reverse('admin_tournament_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tournament 1')
        self.assertNotContains(response, 'Tournament 2')

    def test_org_admin_cannot_edit_other_org_tournament(self):
        self.client.login(username='oa1', password='test123')
        response = self.client.get(reverse('admin_tournament_edit', args=[self.t2.pk]))
        self.assertEqual(response.status_code, 404)

    def test_org_admin_can_edit_own_tournament(self):
        self.client.login(username='oa1', password='test123')
        response = self.client.get(reverse('admin_tournament_edit', args=[self.t1.pk]))
        self.assertEqual(response.status_code, 200)


# ==================== ORG-SCOPED EQUIPMENT VIEW TESTS ====================

class OrgScopedEquipmentViewTests(TestCase):
    """Tests that org_admin users only see/manage their own organization's equipment."""

    def setUp(self):
        self.org1 = Organization.objects.create(name='Org 1', status='approved')
        self.org2 = Organization.objects.create(name='Org 2', status='approved')
        
        self.eq1 = Equipment.objects.create(
            name='Paddle Pro', type='paddle', organization=self.org1,
            quantity_available=5, quantity_total=10, rental_price=50,
            is_active=True
        )
        self.eq2 = Equipment.objects.create(
            name='Premium Paddle', type='paddle', organization=self.org2,
            quantity_available=3, quantity_total=5, rental_price=100,
            is_active=True
        )
        
        self.super_admin = User.objects.create_user(
            username='sa', password='test123', role='super_admin'
        )
        self.org1_admin = User.objects.create_user(
            username='oa1', password='test123', role='org_admin',
            organization=self.org1
        )

    def test_super_admin_sees_all_equipment(self):
        self.client.login(username='sa', password='test123')
        response = self.client.get(reverse('super_admin_equipment_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Paddle Pro')
        self.assertContains(response, 'Premium Paddle')

    def test_org_admin_only_sees_own_equipment(self):
        self.client.login(username='oa1', password='test123')
        response = self.client.get(reverse('super_admin_equipment_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Paddle Pro')
        self.assertNotContains(response, 'Premium Paddle')

    def test_org_admin_cannot_edit_other_org_equipment(self):
        self.client.login(username='oa1', password='test123')
        response = self.client.get(reverse('super_admin_equipment_edit', args=[self.eq2.pk]))
        self.assertEqual(response.status_code, 404)

    def test_org_admin_cannot_delete_other_org_equipment(self):
        self.client.login(username='oa1', password='test123')
        response = self.client.post(reverse('super_admin_equipment_delete', args=[self.eq2.pk]))
        self.assertEqual(response.status_code, 404)

    def test_org_admin_can_edit_own_equipment(self):
        self.client.login(username='oa1', password='test123')
        response = self.client.get(reverse('super_admin_equipment_edit', args=[self.eq1.pk]))
        self.assertEqual(response.status_code, 200)

    def test_org_admin_create_auto_assigns_org(self):
        self.client.login(username='oa1', password='test123')
        response = self.client.post(reverse('super_admin_equipment_create'), {
            'name': 'New Paddle',
            'type': 'paddle',
            'quantity_total': 5,
            'quantity_available': 5,
            'rental_price': 75,
            'condition': 'good',
        })
        self.assertEqual(response.status_code, 302)
        
        new_eq = Equipment.objects.get(name='New Paddle')
        self.assertEqual(new_eq.organization, self.org1)


# ==================== PUBLIC DIRECTORY VIEW TESTS ====================

class PublicDirectoryViewTests(TestCase):
    """Tests for the public organization directory and detail pages."""

    def setUp(self):
        self.approved_org = Organization.objects.create(
            name='Approved Club', status='approved', is_active=True,
            city='Makati', description='Great club!'
        )
        self.pending_org = Organization.objects.create(
            name='Pending Club', status='pending', is_active=True
        )
        self.inactive_org = Organization.objects.create(
            name='Inactive Club', status='approved', is_active=False
        )

    def test_directory_shows_approved_orgs_only(self):
        response = self.client.get(reverse('organization_directory'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Approved Club')
        self.assertNotContains(response, 'Pending Club')
        self.assertNotContains(response, 'Inactive Club')

    def test_directory_search_by_name(self):
        response = self.client.get(reverse('organization_directory'), {'search': 'Approved'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Approved Club')

    def test_directory_search_no_results(self):
        response = self.client.get(reverse('organization_directory'), {'search': 'Nonexistent'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Approved Club')

    def test_public_detail_approved_org(self):
        response = self.client.get(
            reverse('organization_public_detail', args=[self.approved_org.slug])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Approved Club')

    def test_public_detail_pending_org_404(self):
        response = self.client.get(
            reverse('organization_public_detail', args=[self.pending_org.slug])
        )
        self.assertEqual(response.status_code, 404)

    def test_public_detail_inactive_org_404(self):
        response = self.client.get(
            reverse('organization_public_detail', args=[self.inactive_org.slug])
        )
        self.assertEqual(response.status_code, 404)

    def test_registration_page_loads(self):
        response = self.client.get(reverse('organization_register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Register')

    def test_registration_creates_pending_org(self):
        response = self.client.post(reverse('organization_register'), {
            'name': 'Brand New Club',
            'contact_email': 'new@club.com',
            'registration_notes': 'We want to join!',
            'agree_terms': True,
        })
        self.assertEqual(response.status_code, 302)
        
        org = Organization.objects.get(name='Brand New Club')
        self.assertEqual(org.status, 'pending')


# ==================== DASHBOARD REDIRECT TESTS ====================

class DashboardRedirectTests(TestCase):
    """Tests that users are redirected to the correct dashboard based on role."""

    def setUp(self):
        self.org = Organization.objects.create(name='Test Org', status='approved')
        self.super_admin = User.objects.create_user(
            username='sa', password='test123', role='super_admin'
        )
        self.org_admin = User.objects.create_user(
            username='oa', password='test123', role='org_admin',
            organization=self.org
        )
        self.org_staff = User.objects.create_user(
            username='os', password='test123', role='org_staff',
            organization=self.org
        )
        self.regular_user = User.objects.create_user(
            username='user', password='test123', role='user'
        )

    def test_super_admin_redirects_to_super_admin_dashboard(self):
        self.client.login(username='sa', password='test123')
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('super_admin_org_dashboard'))

    def test_org_admin_redirects_to_org_admin_dashboard(self):
        self.client.login(username='oa', password='test123')
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('org_admin_dashboard'))

    def test_org_staff_redirects_to_staff_dashboard(self):
        self.client.login(username='os', password='test123')
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('staff_dashboard'))

    def test_user_redirects_to_user_dashboard(self):
        self.client.login(username='user', password='test123')
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('user_dashboard'))

    def test_login_redirects_super_admin_correctly(self):
        response = self.client.post(reverse('login'), {
            'username': 'sa', 'password': 'test123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('super_admin_org_dashboard'))

    def test_login_redirects_org_admin_correctly(self):
        response = self.client.post(reverse('login'), {
            'username': 'oa', 'password': 'test123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('org_admin_dashboard'))


# ==================== SUPER ADMIN ORGANIZATION FORM TESTS ====================

class SuperAdminOrganizationFormTests(TestCase):
    """Tests for the SuperAdminOrganizationForm used by super admin to create/edit orgs."""

    def setUp(self):
        self.org = Organization.objects.create(name='Existing Org', status='approved')
        self.unassigned_admin = User.objects.create_user(
            username='unassigned_admin', password='test123', role='org_admin'
        )
        self.assigned_admin = User.objects.create_user(
            username='assigned_admin', password='test123', role='org_admin',
            organization=self.org
        )

    def test_form_valid_with_required_only(self):
        """Form should be valid with just the required fields."""
        form_data = {
            'name': 'New Test Organization',
            'status': 'pending',
            'max_staff_accounts': 5,
        }
        form = SuperAdminOrganizationForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_valid_with_all_fields(self):
        """Form should be valid with all fields filled."""
        form_data = {
            'name': 'Full Test Org',
            'description': 'A test org',
            'address': '123 Test St',
            'city': 'Test City',
            'province': 'Test Province',
            'contact_email': 'test@org.com',
            'contact_phone': '555-1234',
            'status': 'approved',
            'is_active': True,
            'max_staff_accounts': 10,
        }
        form = SuperAdminOrganizationForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_empty_name_invalid(self):
        """Form should be invalid without a name."""
        form_data = {}
        form = SuperAdminOrganizationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_create_form_org_admin_queryset_only_unassigned(self):
        """When creating, only unassigned org_admins should appear."""
        form = SuperAdminOrganizationForm()
        admin_choices = list(form.fields['org_admin'].queryset)
        self.assertIn(self.unassigned_admin, admin_choices)
        self.assertNotIn(self.assigned_admin, admin_choices)

    def test_edit_form_org_admin_queryset_includes_current(self):
        """When editing, the currently assigned admin should also appear."""
        form = SuperAdminOrganizationForm(instance=self.org)
        admin_choices = list(form.fields['org_admin'].queryset)
        self.assertIn(self.unassigned_admin, admin_choices)
        self.assertIn(self.assigned_admin, admin_choices)

    def test_edit_form_initial_value_set(self):
        """When editing, the initial value should be the current admin's ID."""
        form = SuperAdminOrganizationForm(instance=self.org)
        self.assertEqual(form.fields['org_admin'].initial, self.assigned_admin.id)

    def test_create_form_initially_empty(self):
        """When creating, the initial value for org_admin should be None."""
        form = SuperAdminOrganizationForm()
        self.assertIsNone(form.fields['org_admin'].initial)

    def test_form_status_defaults_to_pending(self):
        """The status field should default to 'pending'."""
        form = SuperAdminOrganizationForm()
        self.assertEqual(form.fields['status'].initial, 'pending')

    def test_form_returns_org_admin_in_cleaned_data(self):
        """Submitting with org_admin should provide the user in cleaned_data."""
        form_data = {
            'name': 'Org With Admin',
            'status': 'approved',
            'max_staff_accounts': 5,
            'org_admin': self.unassigned_admin.id,
        }
        form = SuperAdminOrganizationForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        org = form.save()
        # The form provides cleaned_data['org_admin'] - view handles actual assignment
        self.assertEqual(form.cleaned_data['org_admin'], self.unassigned_admin)


# ==================== SUPER ADMIN ORG CREATE VIEW TESTS ====================

class SuperAdminCreateOrgViewTests(TestCase):
    """Tests for super_admin_organization_create view."""

    def setUp(self):
        self.super_admin = User.objects.create_user(
            username='sa', password='test123', role='super_admin'
        )
        self.org_admin = User.objects.create_user(
            username='oa', password='test123', role='org_admin'
        )
        self.regular_user = User.objects.create_user(
            username='user', password='test123', role='user'
        )
        self.base_data = {
            'name': 'Created Test Org',
            'description': 'Created in test',
            'address': '456 Create St',
            'city': 'Create City',
            'province': 'Create Prov',
            'contact_email': 'create@test.com',
            'contact_phone': '555-CREATE',
            'status': 'approved',
            'is_active': True,
            'max_staff_accounts': 5,
        }

    def test_create_get_as_super_admin(self):
        """Super admin should see the create form."""
        self.client.login(username='sa', password='test123')
        response = self.client.get(reverse('super_admin_organization_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create New Organization')
        self.assertContains(response, 'Organization name')

    def test_create_get_as_regular_user_blocked(self):
        """Regular users should be redirected away."""
        self.client.login(username='user', password='test123')
        response = self.client.get(reverse('super_admin_organization_create'))
        self.assertEqual(response.status_code, 302)

    def test_create_get_as_org_admin_blocked(self):
        """Org admins should be redirected away."""
        self.client.login(username='oa', password='test123')
        response = self.client.get(reverse('super_admin_organization_create'))
        self.assertEqual(response.status_code, 302)

    def test_create_get_unauthenticated_blocked(self):
        """Unauthenticated users should be redirected to login."""
        response = self.client.get(reverse('super_admin_organization_create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_create_org_success(self):
        """Super admin can create an organization."""
        self.client.login(username='sa', password='test123')
        response = self.client.post(
            reverse('super_admin_organization_create'),
            self.base_data,
            follow=True
        )
        self.assertRedirects(response, reverse('super_admin_organization_list'))
        self.assertTrue(Organization.objects.filter(name='Created Test Org').exists())
        org = Organization.objects.get(name='Created Test Org')
        self.assertEqual(org.status, 'approved')
        self.assertEqual(org.approved_by, self.super_admin)
        self.assertIsNotNone(org.approved_at)

    def test_create_org_with_org_admin(self):
        """Creating an org with an org_admin assigns the user."""
        self.client.login(username='sa', password='test123')
        data = self.base_data.copy()
        data['name'] = 'Org With Admin'
        data['org_admin'] = self.org_admin.id
        response = self.client.post(
            reverse('super_admin_organization_create'),
            data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.org_admin.refresh_from_db()
        self.assertIsNotNone(self.org_admin.organization)
        self.assertEqual(self.org_admin.organization.name, 'Org With Admin')

    def test_create_org_missing_name(self):
        """Creating without a name should show form errors."""
        self.client.login(username='sa', password='test123')
        data = self.base_data.copy()
        data['name'] = ''
        response = self.client.post(
            reverse('super_admin_organization_create'),
            data
        )
        self.assertEqual(response.status_code, 200)  # Re-renders form
        self.assertContains(response, 'This field is required')
        self.assertFalse(Organization.objects.filter(description='Created in test').exists())

    def test_create_org_duplicate_name(self):
        """Creating with a duplicate name should show error."""
        Organization.objects.create(name='Created Test Org')
        self.client.login(username='sa', password='test123')
        response = self.client.post(
            reverse('super_admin_organization_create'),
            self.base_data
        )
        self.assertEqual(response.status_code, 200)
        # Should contain some form of error about the name
        self.assertContains(response, 'already exists', status_code=200)

    def test_create_org_success_message(self):
        """Success message should appear after creation."""
        self.client.login(username='sa', password='test123')
        response = self.client.post(
            reverse('super_admin_organization_create'),
            self.base_data,
            follow=True
        )
        self.assertContains(response, 'created successfully')

    def test_create_org_with_pending_status(self):
        """Creating with pending status should not set approved_by."""
        self.client.login(username='sa', password='test123')
        data = self.base_data.copy()
        data['name'] = 'Pending Created Org'
        data['status'] = 'pending'
        response = self.client.post(
            reverse('super_admin_organization_create'),
            data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        org = Organization.objects.get(name='Pending Created Org')
        self.assertEqual(org.status, 'pending')
        self.assertIsNone(org.approved_by)
        self.assertIsNone(org.approved_at)


# ==================== SUPER ADMIN ORG EDIT VIEW TESTS ====================

class SuperAdminEditOrgViewTests(TestCase):
    """Tests for super_admin_organization_edit view."""

    def setUp(self):
        self.super_admin = User.objects.create_user(
            username='sa', password='test123', role='super_admin'
        )
        self.org_admin = User.objects.create_user(
            username='oa', password='test123', role='org_admin'
        )
        self.regular_user = User.objects.create_user(
            username='user', password='test123', role='user'
        )
        self.org = Organization.objects.create(
            name='Edit Test Org',
            description='Original description',
            status='pending',
        )
        self.edit_data = {
            'name': 'Edit Test Org Updated',
            'description': 'Updated description',
            'address': '789 Edit Ave',
            'city': 'Edit City',
            'province': 'Edit Prov',
            'contact_email': 'edit@test.com',
            'contact_phone': '555-EDIT',
            'status': 'approved',
            'is_active': True,
            'max_staff_accounts': 10,
        }

    def test_edit_get_as_super_admin(self):
        """Super admin should see the edit form."""
        self.client.login(username='sa', password='test123')
        response = self.client.get(
            reverse('super_admin_organization_edit', args=[self.org.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Organization')
        self.assertContains(response, self.org.name)

    def test_edit_get_nonexistent_org_404(self):
        """Editing a non-existent org should 404."""
        self.client.login(username='sa', password='test123')
        response = self.client.get(
            reverse('super_admin_organization_edit', args=[999])
        )
        self.assertEqual(response.status_code, 404)

    def test_edit_get_as_regular_user_blocked(self):
        """Regular users cannot access edit form."""
        self.client.login(username='user', password='test123')
        response = self.client.get(
            reverse('super_admin_organization_edit', args=[self.org.pk])
        )
        self.assertEqual(response.status_code, 302)

    def test_edit_org_success(self):
        """Super admin can edit an organization."""
        self.client.login(username='sa', password='test123')
        response = self.client.post(
            reverse('super_admin_organization_edit', args=[self.org.pk]),
            self.edit_data,
            follow=True
        )
        self.assertRedirects(response, reverse('super_admin_organization_list'))
        self.org.refresh_from_db()
        self.assertEqual(self.org.name, 'Edit Test Org Updated')
        self.assertEqual(self.org.description, 'Updated description')
        self.assertEqual(self.org.status, 'approved')
        self.assertEqual(self.org.max_staff_accounts, 10)
        self.assertEqual(self.org.approved_by, self.super_admin)
        self.assertIsNotNone(self.org.approved_at)

    def test_edit_org_suspend(self):
        """Super admin can suspend an organization."""
        self.client.login(username='sa', password='test123')
        data = self.edit_data.copy()
        data['name'] = 'Edit Test Org'  # Keep same name
        data['status'] = 'suspended'
        response = self.client.post(
            reverse('super_admin_organization_edit', args=[self.org.pk]),
            data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.org.refresh_from_db()
        self.assertEqual(self.org.status, 'suspended')

    def test_edit_org_assign_admin(self):
        """Editing can assign an org_admin to the organization."""
        self.client.login(username='sa', password='test123')
        data = self.edit_data.copy()
        data['name'] = 'Edit Test Org'
        data['org_admin'] = self.org_admin.id
        response = self.client.post(
            reverse('super_admin_organization_edit', args=[self.org.pk]),
            data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.org_admin.refresh_from_db()
        self.assertEqual(self.org_admin.organization, self.org)

    def test_edit_org_reassign_admin(self):
        """Editing can reassign a different org_admin."""
        old_admin = User.objects.create_user(
            username='old_admin', password='test123', role='org_admin',
            organization=self.org
        )
        new_admin = User.objects.create_user(
            username='new_admin', password='test123', role='org_admin'
        )
        self.client.login(username='sa', password='test123')
        data = self.edit_data.copy()
        data['name'] = 'Edit Test Org'
        data['org_admin'] = new_admin.id
        response = self.client.post(
            reverse('super_admin_organization_edit', args=[self.org.pk]),
            data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        old_admin.refresh_from_db()
        new_admin.refresh_from_db()
        self.assertIsNone(old_admin.organization)  # Old admin unassigned
        self.assertEqual(new_admin.organization, self.org)  # New admin assigned

    def test_edit_org_remove_admin(self):
        """Editing can remove the org_admin by not selecting one."""
        User.objects.create_user(
            username='current_admin', password='test123', role='org_admin',
            organization=self.org
        )
        self.client.login(username='sa', password='test123')
        data = self.edit_data.copy()
        data['name'] = 'Edit Test Org'
        # Don't include org_admin in data
        data.pop('org_admin', None)
        response = self.client.post(
            reverse('super_admin_organization_edit', args=[self.org.pk]),
            data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        # The current admin should be unassigned when no admin is selected
        current_admin = User.objects.get(username='current_admin')
        self.assertIsNone(current_admin.organization)

    def test_edit_org_success_message(self):
        """Success message should appear after edit."""
        self.client.login(username='sa', password='test123')
        response = self.client.post(
            reverse('super_admin_organization_edit', args=[self.org.pk]),
            self.edit_data,
            follow=True
        )
        self.assertContains(response, 'updated successfully')

    def test_edit_edit_mode_in_context(self):
        """The template should receive edit_mode=True."""
        self.client.login(username='sa', password='test123')
        response = self.client.get(
            reverse('super_admin_organization_edit', args=[self.org.pk])
        )
        self.assertEqual(response.context.get('edit_mode'), True)
        self.assertIsNotNone(response.context.get('organization'))


# ==================== SUPER ADMIN ORG DELETE VIEW TESTS ====================

class SuperAdminDeleteOrgViewTests(TestCase):
    """Tests for super_admin_organization_delete view."""

    def setUp(self):
        self.super_admin = User.objects.create_user(
            username='sa', password='test123', role='super_admin'
        )
        self.org_admin = User.objects.create_user(
            username='oa', password='test123', role='org_admin'
        )
        self.regular_user = User.objects.create_user(
            username='user', password='test123', role='user'
        )
        self.org = Organization.objects.create(
            name='Delete Test Org',
            status='approved',
        )
        self.site = Site.objects.create(name='Test Site', organization=self.org)
        self.court = Court.objects.create(
            name='Test Court', site=self.site, organization=self.org,
            is_active=True, hourly_rate=100
        )

    def test_delete_get_confirmation_page(self):
        """GET should show the delete confirmation page."""
        self.client.login(username='sa', password='test123')
        response = self.client.get(
            reverse('super_admin_organization_delete', args=[self.org.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Confirm Deletion')
        self.assertContains(response, self.org.name)

    def test_delete_get_nonexistent_org_404(self):
        """Deleting a non-existent org should 404."""
        self.client.login(username='sa', password='test123')
        response = self.client.get(
            reverse('super_admin_organization_delete', args=[999])
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_get_as_regular_user_blocked(self):
        """Regular users cannot access delete page."""
        self.client.login(username='user', password='test123')
        response = self.client.get(
            reverse('super_admin_organization_delete', args=[self.org.pk])
        )
        self.assertEqual(response.status_code, 302)

    def test_delete_org_without_active_data(self):
        """Super admin can delete an org with no active reservations/tournaments."""
        self.client.login(username='sa', password='test123')
        response = self.client.post(
            reverse('super_admin_organization_delete', args=[self.org.pk]),
            follow=True
        )
        self.assertRedirects(response, reverse('super_admin_organization_list'))
        self.assertFalse(Organization.objects.filter(pk=self.org.pk).exists())

    def test_delete_org_unassigns_members(self):
        """Deleting an org should unassign all members."""
        staff_user = User.objects.create_user(
            username='staff', password='test123', role='org_staff',
            organization=self.org
        )
        self.client.login(username='sa', password='test123')
        self.client.post(
            reverse('super_admin_organization_delete', args=[self.org.pk]),
            follow=True
        )
        staff_user.refresh_from_db()
        self.assertIsNone(staff_user.organization)

    def test_delete_org_success_message(self):
        """Success message should appear after deletion."""
        self.client.login(username='sa', password='test123')
        response = self.client.post(
            reverse('super_admin_organization_delete', args=[self.org.pk]),
            follow=True
        )
        self.assertContains(response, 'permanently deleted')

    def test_delete_blocked_with_active_reservation(self):
        """Deletion should be blocked when org has active reservations."""
        test_user = User.objects.create_user(
            username='res_user', password='test123', role='user'
        )
        from datetime import time, date, timedelta
        Reservation.objects.create(
            user=test_user,
            court=self.court,
            date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(11, 0),
            hourly_rate=20,
            subtotal=20,
            total_amount=20,
            status='confirmed'
        )
        self.client.login(username='sa', password='test123')
        response = self.client.post(
            reverse('super_admin_organization_delete', args=[self.org.pk]),
            follow=True
        )
        # Should be redirected back without deleting
        self.assertTrue(Organization.objects.filter(pk=self.org.pk).exists())
        self.assertContains(response, 'Cannot delete')
        self.assertContains(response, 'active reservation')

    def test_delete_blocked_with_active_tournament(self):
        """Deletion should be blocked when org has active tournaments."""
        from django.utils import timezone
        from datetime import timedelta
        Tournament.objects.create(
            name='Active Tournament', organization=self.org,
            category='singles', format='round_robin',
            registration_start=timezone.now(),
            registration_end=timezone.now() + timedelta(days=10),
            tournament_start=timezone.now() + timedelta(days=20),
            tournament_end=timezone.now() + timedelta(days=22),
            status='in_progress'
        )
        self.client.login(username='sa', password='test123')
        response = self.client.post(
            reverse('super_admin_organization_delete', args=[self.org.pk]),
            follow=True
        )
        self.assertTrue(Organization.objects.filter(pk=self.org.pk).exists())
        self.assertContains(response, 'Cannot delete')
        self.assertContains(response, 'active tournament')

    def test_delete_blocked_with_pending_payment(self):
        """Deletion should be blocked when org has pending payments."""
        test_user = User.objects.create_user(
            username='pay_user', password='test123', role='user'
        )
        from datetime import time, date, timedelta
        res = Reservation.objects.create(
            user=test_user,
            court=self.court,
            date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(11, 0),
            hourly_rate=20,
            subtotal=20,
            total_amount=20,
            status='confirmed'
        )
        Payment.objects.create(
            reservation=res,
            amount=20,
            status='pending',
            method='gcash',
        )
        self.client.login(username='sa', password='test123')
        response = self.client.post(
            reverse('super_admin_organization_delete', args=[self.org.pk]),
            follow=True
        )
        self.assertTrue(Organization.objects.filter(pk=self.org.pk).exists())
        self.assertContains(response, 'Cannot delete')
        self.assertContains(response, 'pending')

    def test_delete_confirmation_shows_blocked_state(self):
        """The confirmation page should show blocked state when active data exists."""
        test_user = User.objects.create_user(
            username='block_user', password='test123', role='user'
        )
        from datetime import time, date, timedelta
        Reservation.objects.create(
            user=test_user,
            court=self.court,
            date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(11, 0),
            hourly_rate=20,
            subtotal=20,
            total_amount=20,
            status='confirmed'
        )
        self.client.login(username='sa', password='test123')
        response = self.client.get(
            reverse('super_admin_organization_delete', args=[self.org.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Deletion Blocked')
        self.assertContains(response, 'active reservation')
        self.assertIn('has_active_data', response.context)
        self.assertTrue(response.context['has_active_data'])
        self.assertEqual(response.context['active_reservation_count'], 1)

    def test_delete_completed_reservation_does_not_block(self):
        """Completed/cancelled reservations should not block deletion."""
        test_user = User.objects.create_user(
            username='past_user', password='test123', role='user'
        )
        from datetime import time, date, timedelta
        Reservation.objects.create(
            user=test_user,
            court=self.court,
            date=date.today() - timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(11, 0),
            hourly_rate=20,
            subtotal=20,
            total_amount=20,
            status='completed'
        )
        self.client.login(username='sa', password='test123')
        response = self.client.post(
            reverse('super_admin_organization_delete', args=[self.org.pk]),
            follow=True
        )
        self.assertRedirects(response, reverse('super_admin_organization_list'))
        self.assertFalse(Organization.objects.filter(pk=self.org.pk).exists())


# ==================== SUPER ADMIN ORG LIST VIEW TESTS ====================

class SuperAdminOrgListViewTests(TestCase):
    """Tests for super_admin_organization_list view."""

    def setUp(self):
        self.super_admin = User.objects.create_user(
            username='sa', password='test123', role='super_admin'
        )
        self.org1 = Organization.objects.create(
            name='Alpha Org', status='approved', city='Manila'
        )
        self.org2 = Organization.objects.create(
            name='Beta Club', status='pending', city='Cebu'
        )
        self.org3 = Organization.objects.create(
            name='Gamma Center', status='suspended', city='Manila'
        )

    def test_list_get_as_super_admin(self):
        """Super admin should see the organization list."""
        self.client.login(username='sa', password='test123')
        response = self.client.get(reverse('super_admin_organization_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alpha Org')
        self.assertContains(response, 'Beta Club')
        self.assertContains(response, 'Gamma Center')

    def test_list_get_as_regular_user_blocked(self):
        """Regular users cannot see the list."""
        regular_user = User.objects.create_user(
            username='user', password='test123', role='user'
        )
        self.client.login(username='user', password='test123')
        response = self.client.get(reverse('super_admin_organization_list'))
        self.assertEqual(response.status_code, 302)

    def test_list_search_by_name(self):
        """Search should filter by name."""
        self.client.login(username='sa', password='test123')
        response = self.client.get(
            reverse('super_admin_organization_list'),
            {'search': 'Alpha'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alpha Org')
        self.assertNotContains(response, 'Beta Club')
        self.assertNotContains(response, 'Gamma Center')

    def test_list_search_by_city(self):
        """Search should filter by city."""
        self.client.login(username='sa', password='test123')
        response = self.client.get(
            reverse('super_admin_organization_list'),
            {'search': 'Cebu'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Beta Club')
        self.assertNotContains(response, 'Alpha Org')

    def test_list_search_no_results(self):
        """Search with no matches should show empty results."""
        self.client.login(username='sa', password='test123')
        response = self.client.get(
            reverse('super_admin_organization_list'),
            {'search': 'Nonexistent'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Alpha Org')
        self.assertNotContains(response, 'Beta Club')

    def test_list_filter_by_status(self):
        """Status filter should work."""
        self.client.login(username='sa', password='test123')
        response = self.client.get(
            reverse('super_admin_organization_list'),
            {'status': 'pending'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Alpha Org')
        self.assertContains(response, 'Beta Club')
        self.assertNotContains(response, 'Gamma Center')

    def test_list_filter_suspended(self):
        """Filtering by suspended status should work."""
        self.client.login(username='sa', password='test123')
        response = self.client.get(
            reverse('super_admin_organization_list'),
            {'status': 'suspended'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Alpha Org')
        self.assertNotContains(response, 'Beta Club')
        self.assertContains(response, 'Gamma Center')

    def test_list_sort_by_name_asc(self):
        """Sorting by name ascending should work."""
        self.client.login(username='sa', password='test123')
        response = self.client.get(
            reverse('super_admin_organization_list'),
            {'sort_by': 'name', 'sort_order': 'asc'}
        )
        self.assertEqual(response.status_code, 200)
        # Check order: Alpha < Beta < Gamma
        content = response.content.decode()
        self.assertLess(content.index('Alpha Org'), content.index('Beta Club'))
        self.assertLess(content.index('Beta Club'), content.index('Gamma Center'))

    def test_list_sort_by_name_desc(self):
        """Sorting by name descending should work."""
        self.client.login(username='sa', password='test123')
        response = self.client.get(
            reverse('super_admin_organization_list'),
            {'sort_by': 'name', 'sort_order': 'desc'}
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertGreater(content.index('Alpha Org'), content.index('Gamma Center'))

    def test_list_sort_by_created_at(self):
        """Sorting by created_at should work."""
        self.client.login(username='sa', password='test123')
        response = self.client.get(
            reverse('super_admin_organization_list'),
            {'sort_by': '-created_at', 'sort_order': 'desc'}
        )
        self.assertEqual(response.status_code, 200)

    def test_list_stats_in_context(self):
        """Stats should be in the template context."""
        self.client.login(username='sa', password='test123')
        response = self.client.get(reverse('super_admin_organization_list'))
        self.assertIn('stats', response.context)
        stats = response.context['stats']
        self.assertEqual(stats['total'], 4)
        self.assertEqual(stats['pending'], 1)
        self.assertEqual(stats['approved'], 2)
        self.assertEqual(stats['suspended'], 1)

    def test_list_pagination_present(self):
        """Pagination should be available in the context."""
        self.client.login(username='sa', password='test123')
        response = self.client.get(reverse('super_admin_organization_list'))
        self.assertIn('is_paginated', response.context)
        self.assertIn('page_obj', response.context)


# ==================== SUPER ADMIN ORG DETAIL VIEW TESTS ====================

class SuperAdminOrgDetailViewTests(TestCase):
    """Tests for super_admin_organization_detail view."""

    def setUp(self):
        self.super_admin = User.objects.create_user(
            username='sa', password='test123', role='super_admin'
        )
        self.org_admin_user = User.objects.create_user(
            username='oa_assigned', password='test123', role='org_admin'
        )
        self.regular_user = User.objects.create_user(
            username='user', password='test123', role='user'
        )
        self.org = Organization.objects.create(
            name='Detail Test Org',
            description='Detail description',
            city='Detail City',
            province='Detail Province',
            contact_email='detail@test.com',
            contact_phone='555-DETAIL',
            status='approved',
        )
        self.site = Site.objects.create(name='Detail Site', organization=self.org)
        self.court = Court.objects.create(
            name='Detail Court', site=self.site, organization=self.org,
            is_active=True, hourly_rate=100
        )
        # Assign org_admin
        self.org_admin_user.organization = self.org
        self.org_admin_user.save()

    def test_detail_get_as_super_admin(self):
        """Super admin should see the detail page."""
        self.client.login(username='sa', password='test123')
        response = self.client.get(
            reverse('super_admin_organization_detail', args=[self.org.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Detail Test Org')
        self.assertContains(response, 'Detail City')

    def test_detail_get_nonexistent_org_404(self):
        """Non-existent org should 404."""
        self.client.login(username='sa', password='test123')
        response = self.client.get(
            reverse('super_admin_organization_detail', args=[999])
        )
        self.assertEqual(response.status_code, 404)

    def test_detail_get_as_regular_user_blocked(self):
        """Regular users cannot access detail page."""
        self.client.login(username='user', password='test123')
        response = self.client.get(
            reverse('super_admin_organization_detail', args=[self.org.pk])
        )
        self.assertEqual(response.status_code, 302)

    def test_detail_shows_court_count(self):
        """Detail page should show the number of courts."""
        self.client.login(username='sa', password='test123')
        response = self.client.get(
            reverse('super_admin_organization_detail', args=[self.org.pk])
        )
        # The court count should be visible
        self.assertContains(response, 'Detail Court')

    def test_detail_shows_org_admin(self):
        """Detail page should show the assigned org_admin."""
        self.client.login(username='sa', password='test123')
        response = self.client.get(
            reverse('super_admin_organization_detail', args=[self.org.pk])
        )
        self.assertContains(response, 'oa_assigned')
        self.assertIn('org_admin_user', response.context)
        self.assertEqual(response.context['org_admin_user'], self.org_admin_user)

    def test_detail_context_has_courts_tournaments(self):
        """Context should include courts and tournaments."""
        self.client.login(username='sa', password='test123')
        response = self.client.get(
            reverse('super_admin_organization_detail', args=[self.org.pk])
        )
        self.assertIn('courts', response.context)
        self.assertIn('tournaments', response.context)
        self.assertIn('staff_members', response.context)
