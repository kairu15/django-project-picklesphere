from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta

from .models import Organization
from .forms import OrganizationRegistrationForm, OrganizationApprovalForm, OrganizationProfileForm
from accounts.models import User
from accounts.decorators import super_admin_required, org_admin_required, org_required
from courts.models import Court, Site
from tournaments.models import Tournament
from equipment.models import Equipment


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
        response = self.client.get(reverse('admin_court_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Court A')
        self.assertContains(response, 'Court B')

    def test_org1_admin_only_sees_own_courts(self):
        self.client.login(username='oa1', password='test123')
        response = self.client.get(reverse('admin_court_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Court A')
        self.assertNotContains(response, 'Court B')

    def test_org2_admin_only_sees_own_courts(self):
        self.client.login(username='oa2', password='test123')
        response = self.client.get(reverse('admin_court_list'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Court A')
        self.assertContains(response, 'Court B')

    def test_org_admin_cannot_edit_other_org_court(self):
        self.client.login(username='oa1', password='test123')
        # Trying to edit court2 (belongs to org2) should 404
        response = self.client.get(reverse('admin_court_edit', args=[self.court2.pk]))
        self.assertEqual(response.status_code, 404)

    def test_org_admin_can_edit_own_court(self):
        self.client.login(username='oa1', password='test123')
        response = self.client.get(reverse('admin_court_edit', args=[self.court1.pk]))
        self.assertEqual(response.status_code, 200)

    def test_org_admin_cannot_delete_other_org_court(self):
        self.client.login(username='oa1', password='test123')
        # POST to delete court2
        response = self.client.post(reverse('admin_court_delete', args=[self.court2.pk]))
        self.assertEqual(response.status_code, 404)

    def test_super_admin_can_delete_any_court(self):
        self.client.login(username='sa', password='test123')
        response = self.client.post(reverse('admin_court_delete', args=[self.court2.pk]))
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
        response = self.client.get(reverse('admin_equipment_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Paddle Pro')
        self.assertContains(response, 'Premium Paddle')

    def test_org_admin_only_sees_own_equipment(self):
        self.client.login(username='oa1', password='test123')
        response = self.client.get(reverse('admin_equipment_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Paddle Pro')
        self.assertNotContains(response, 'Premium Paddle')

    def test_org_admin_cannot_edit_other_org_equipment(self):
        self.client.login(username='oa1', password='test123')
        response = self.client.get(reverse('admin_equipment_edit', args=[self.eq2.pk]))
        self.assertEqual(response.status_code, 404)

    def test_org_admin_cannot_delete_other_org_equipment(self):
        self.client.login(username='oa1', password='test123')
        response = self.client.post(reverse('admin_equipment_delete', args=[self.eq2.pk]))
        self.assertEqual(response.status_code, 404)

    def test_org_admin_can_edit_own_equipment(self):
        self.client.login(username='oa1', password='test123')
        response = self.client.get(reverse('admin_equipment_edit', args=[self.eq1.pk]))
        self.assertEqual(response.status_code, 200)

    def test_org_admin_create_auto_assigns_org(self):
        self.client.login(username='oa1', password='test123')
        response = self.client.post(reverse('admin_equipment_create'), {
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
        self.assertRedirects(response, reverse('super_admin_dashboard'))

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
        self.assertEqual(response.url, reverse('super_admin_dashboard'))

    def test_login_redirects_org_admin_correctly(self):
        response = self.client.post(reverse('login'), {
            'username': 'oa', 'password': 'test123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('org_admin_dashboard'))
