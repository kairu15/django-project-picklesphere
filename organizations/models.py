from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.utils import timezone


class Organization(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    )

    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='organizations/logos/', blank=True, null=True)
    banner = models.ImageField(upload_to='organizations/banners/', blank=True, null=True)
    
    # Contact & Location
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    province = models.CharField(max_length=100, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    
    # Map Location
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, help_text='Latitude coordinate from map picker')
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, help_text='Longitude coordinate from map picker')
    location_address = models.TextField(blank=True, null=True, help_text='Full address resolved from map coordinates')
    
    # Registration / Approval
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    registration_notes = models.TextField(blank=True, null=True, help_text="Why the organization wants to join the platform")
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='approved_organizations'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Verification badge
    is_verified = models.BooleanField(
        default=False,
        help_text='Verified organizations get a badge on their public profile'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='verified_organizations'
    )
    
    # Operating details
    operating_hours = models.TextField(blank=True, null=True, help_text="Operating hours description (e.g., Mon-Fri 6AM-10PM)")
    
    # Settings
    is_active = models.BooleanField(default=True)
    max_staff_accounts = models.PositiveIntegerField(default=5, help_text="Maximum number of staff accounts allowed")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'organizations'
        ordering = ['name']
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'
        indexes = [
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['city', 'is_active']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Ensure uniqueness
            original_slug = self.slug
            counter = 1
            while Organization.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    @property
    def is_approved(self):
        return self.status == 'approved'

    @property
    def is_pending(self):
        return self.status == 'pending'

    @property
    def is_suspended(self):
        return self.status == 'suspended'

    @property
    def court_count(self):
        return self.courts.filter(is_active=True).count()

    @property
    def tournament_count(self):
        return self.tournaments.count()

    @property
    def staff_count(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.filter(organization=self, role='org_staff').count()

    @property
    def total_reservations(self):
        from reservations.models import Reservation
        return Reservation.objects.filter(court__organization=self).exclude(status='cancelled').count()

    def can_add_staff(self):
        return self.staff_count < self.max_staff_accounts

    @property
    def payment_settings_info(self):
        """Return the org's payment settings or None if not configured yet."""
        return getattr(self, 'payment_settings', None)


class OrganizationPaymentSettings(models.Model):
    """
    Organization-specific payment information shown to users on the checkout page.
    Managed exclusively by the Organization Admin (super admins only view status).
    """

    PAYMENT_METHOD_CHOICES = [
        ('gcash', 'GCash'),
        ('maya', 'Maya'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
    ]

    organization = models.OneToOneField(
        Organization, on_delete=models.CASCADE,
        related_name='payment_settings'
    )

    # GCash
    gcash_number = models.CharField(
        max_length=20, blank=True, null=True,
        help_text='GCash mobile number shown to users when paying'
    )
    gcash_account_name = models.CharField(
        max_length=100, blank=True, null=True,
        help_text='Name registered on the GCash account'
    )

    # Maya
    maya_number = models.CharField(
        max_length=20, blank=True, null=True,
        help_text='Maya mobile number shown to users when paying'
    )
    maya_account_name = models.CharField(
        max_length=100, blank=True, null=True,
        help_text='Name registered on the Maya account'
    )

    # Bank Transfer
    bank_name = models.CharField(
        max_length=100, blank=True, null=True,
        help_text='e.g. BDO, BPI, UnionBank'
    )
    bank_account_name = models.CharField(max_length=100, blank=True, null=True)
    bank_account_number = models.CharField(max_length=50, blank=True, null=True)

    # QR Code
    qr_code = models.ImageField(
        upload_to='organizations/payment_qr/', blank=True, null=True,
        help_text='QR code image for payments (shown on the checkout page)'
    )

    # Instructions & Accepted Methods
    payment_instructions = models.TextField(
        blank=True, null=True,
        help_text='Step-by-step instructions shown to users when paying'
    )
    accepted_payment_methods = models.JSONField(
        default=list, blank=True,
        help_text='Payment methods this organization accepts'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Enable online payment submissions for this organization'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'organization_payment_settings'
        verbose_name = 'Organization Payment Settings'
        verbose_name_plural = 'Organization Payment Settings'

    def __str__(self):
        return f'Payment Settings - {self.organization.name}'

    @property
    def has_gcash(self):
        return bool(self.gcash_number and self.gcash_account_name)

    @property
    def has_maya(self):
        return bool(self.maya_number and self.maya_account_name)

    @property
    def has_bank(self):
        return bool(self.bank_name and self.bank_account_name and self.bank_account_number)

    @property
    def is_configured(self):
        """True when at least one complete payment account has been configured."""
        return any([self.has_gcash, self.has_maya, self.has_bank])

    def accepts(self, method):
        return method in (self.accepted_payment_methods or [])

    @property
    def enabled_methods(self):
        """Accepted methods that are fully configured and can be offered at checkout.
        Returns an empty list when online payments are disabled for the organization."""
        if not self.is_active:
            return []
        methods = self.accepted_payment_methods or []
        result = []
        if 'gcash' in methods and self.has_gcash:
            result.append('gcash')
        if 'maya' in methods and self.has_maya:
            result.append('maya')
        if 'bank_transfer' in methods and self.has_bank:
            result.append('bank_transfer')
        return result


class OrganizationAuditLog(models.Model):
    """Audit log for tracking all organization-related actions by admins."""
    ACTION_CHOICES = [
        ('created', 'Organization Created'),
        ('approved', 'Organization Approved'),
        ('rejected', 'Organization Rejected'),
        ('suspended', 'Organization Suspended'),
        ('reactivated', 'Organization Reactivated'),
        ('verified', 'Organization Verified'),
        ('unverified', 'Organization Unverified'),
        ('updated', 'Organization Updated'),
        ('status_changed', 'Status Changed'),
        ('admin_assigned', 'Org Admin Assigned'),
        ('admin_removed', 'Org Admin Removed'),
        ('staff_added', 'Staff Added'),
        ('staff_removed', 'Staff Removed'),
        ('deleted', 'Organization Deleted'),
        ('settings_changed', 'Settings Changed'),
        ('other', 'Other'),
    ]

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='org_audit_actions'
    )
    details = models.TextField(blank=True, null=True, help_text='Description of what was done')
    changes = models.JSONField(blank=True, null=True, help_text='JSON with before/after values of changed fields')
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'organization_audit_logs'
        ordering = ['-created_at']
        verbose_name = 'Organization Audit Log'
        verbose_name_plural = 'Organization Audit Logs'
        indexes = [
            models.Index(fields=['organization', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]

    def __str__(self):
        return f"{self.get_action_display()} - {self.organization.name} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
