from django.db import models
from django.utils.text import slugify
from django.conf import settings


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
    
    # Registration / Approval
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    registration_notes = models.TextField(blank=True, null=True, help_text="Why the organization wants to join the platform")
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='approved_organizations'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
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
