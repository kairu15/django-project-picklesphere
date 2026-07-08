from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError


class PricingContent(models.Model):
    """Editable content sections for the pricing page"""
    SECTION_CHOICES = [
        ('hero_badge', 'Hero Badge'),
        ('hero_title', 'Hero Title'),
        ('hero_subtitle', 'Hero Subtitle'),
        ('court_rates_title', 'Court Rates Section Title'),
        ('court_rates_subtitle', 'Court Rates Section Subtitle'),
        ('membership_title', 'Membership Section Title'),
        ('membership_subtitle', 'Membership Section Subtitle'),
        ('comparison_title', 'Comparison Table Title'),
        ('comparison_subtitle', 'Comparison Table Subtitle'),
        ('services_title', 'Additional Services Title'),
        ('services_subtitle', 'Additional Services Subtitle'),
        ('faq_title', 'FAQ Section Title'),
        ('faq_subtitle', 'FAQ Section Subtitle'),
        ('cta_title', 'CTA Section Title'),
        ('cta_subtitle', 'CTA Section Subtitle'),
    ]
    
    section = models.CharField(max_length=50, choices=SECTION_CHOICES, unique=True)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pricing Page Content'
        verbose_name_plural = 'Pricing Page Contents'
        ordering = ['section']

    def __str__(self):
        return self.get_section_display()


class PricingTier(models.Model):
    """Membership tiers for pricing page"""
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    period = models.CharField(max_length=50, blank=True, help_text="e.g., 'month', 'year', or leave blank for one-time")
    description = models.TextField(blank=True)
    features = models.JSONField(default=list, help_text="List of features as strings")
    is_recommended = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'price']
        verbose_name = 'Pricing Tier'
        verbose_name_plural = 'Pricing Tiers'

    def __str__(self):
        return self.name


class PricingFAQ(models.Model):
    """FAQ items for pricing page"""
    question = models.CharField(max_length=200)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', '-created_at']
        verbose_name = 'Pricing FAQ'
        verbose_name_plural = 'Pricing FAQs'

    def __str__(self):
        return self.question


class AboutContent(models.Model):
    """Editable content sections for the about page"""
    SECTION_CHOICES = [
        ('hero_badge', 'Hero Badge'),
        ('hero_title', 'Hero Title'),
        ('hero_subtitle', 'Hero Subtitle'),
        ('mission_title', 'Mission Section Title'),
        ('mission_text', 'Mission Text'),
        ('mission_features', 'Mission Features (comma-separated)'),
        ('vision_title', 'Vision Section Title'),
        ('vision_text', 'Vision Text'),
        ('vision_features', 'Vision Features (comma-separated)'),
        ('stats_courts', 'Stats - Courts Label'),
        ('stats_members', 'Stats - Members Label'),
        ('stats_years', 'Stats - Years Label'),
        ('stats_tournaments', 'Stats - Tournaments Label'),
        ('journey_badge', 'Journey Section Badge'),
        ('journey_title', 'Journey Section Title'),
        ('journey_subtitle', 'Journey Section Subtitle'),
        ('team_badge', 'Team Section Badge'),
        ('team_title', 'Team Section Title'),
        ('team_subtitle', 'Team Section Subtitle'),
        ('facilities_badge', 'Facilities Section Badge'),
        ('facilities_title', 'Facilities Section Title'),
        ('facilities_subtitle', 'Facilities Section Subtitle'),
        ('why_badge', 'Why Choose Us Badge'),
        ('why_title', 'Why Choose Us Title'),
        ('why_subtitle', 'Why Choose Us Subtitle'),
        ('gallery_badge', 'Gallery Section Badge'),
        ('gallery_title', 'Gallery Section Title'),
        ('gallery_subtitle', 'Gallery Section Subtitle'),
        ('location_badge', 'Location Section Badge'),
        ('location_title', 'Location Section Title'),
        ('location_description', 'Location Description'),
        ('cta_title', 'CTA Section Title'),
        ('cta_subtitle', 'CTA Section Subtitle'),
    ]
    
    section = models.CharField(max_length=50, choices=SECTION_CHOICES, unique=True)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'About Page Content'
        verbose_name_plural = 'About Page Contents'
        ordering = ['section']

    def __str__(self):
        return self.get_section_display()


class Milestone(models.Model):
    """Timeline milestones for about page"""
    year = models.CharField(max_length=20)
    title = models.CharField(max_length=100)
    description = models.TextField()
    color = models.CharField(max_length=50, default='primary', help_text="Bootstrap color name: primary, success, warning, info, danger")
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'year']
        verbose_name = 'Milestone'
        verbose_name_plural = 'Milestones'

    def __str__(self):
        return f"{self.year} - {self.title}"


class TeamMember(models.Model):
    """Team members for about page"""
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    bio = models.TextField()
    photo = models.ImageField(upload_to='team/', blank=True, null=True)
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    color = models.CharField(max_length=50, default='primary', help_text="Bootstrap color name for styling")
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = 'Team Member'
        verbose_name_plural = 'Team Members'

    def __str__(self):
        return f"{self.name} - {self.role}"


class Facility(models.Model):
    """Facilities for about page"""
    icon = models.CharField(max_length=50, default='fa-check', help_text="Font Awesome icon class")
    title = models.CharField(max_length=100)
    description = models.TextField()
    color = models.CharField(max_length=50, default='primary', help_text="Bootstrap color name")
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'title']
        verbose_name = 'Facility'
        verbose_name_plural = 'Facilities'

    def __str__(self):
        return self.title


class WhyChooseItem(models.Model):
    """Why Choose Us items for about page"""
    icon = models.CharField(max_length=50, default='fa-check', help_text="Font Awesome icon class")
    title = models.CharField(max_length=100)
    description = models.TextField()
    color = models.CharField(max_length=50, default='primary', help_text="Bootstrap color name")
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'title']
        verbose_name = 'Why Choose Item'
        verbose_name_plural = 'Why Choose Items'

    def __str__(self):
        return self.title


class ContactContent(models.Model):
    """Editable content sections for the contact page"""
    SECTION_CHOICES = [
        ('hero_badge', 'Hero Badge'),
        ('hero_title', 'Hero Title'),
        ('hero_subtitle', 'Hero Subtitle'),
        ('phone_label', 'Phone Card Label'),
        ('phone_hours', 'Phone Card Hours'),
        ('email_label', 'Email Card Label'),
        ('email_response', 'Email Response Time'),
        ('visit_label', 'Visit Card Label'),
        ('visit_city', 'Visit City'),
        ('form_title', 'Contact Form Title'),
        ('form_name_label', 'Form - Name Label'),
        ('form_email_label', 'Form - Email Label'),
        ('form_subject_label', 'Form - Subject Label'),
        ('form_message_label', 'Form - Message Label'),
        ('form_submit_text', 'Form Submit Button Text'),
        ('hours_title', 'Business Hours Title'),
        ('quick_links_title', 'Quick Links Title'),
        ('social_title', 'Social Media Title'),
        ('map_badge', 'Map Section Badge'),
        ('map_title', 'Map Section Title'),
        ('map_subtitle', 'Map Section Subtitle'),
        ('getting_here_title', 'Getting Here Title'),
        ('faq_badge', 'FAQ Section Badge'),
        ('faq_title', 'FAQ Section Title'),
        ('faq_subtitle', 'FAQ Section Subtitle'),
        ('cta_title', 'CTA Section Title'),
        ('cta_subtitle', 'CTA Section Subtitle'),
    ]
    
    section = models.CharField(max_length=50, choices=SECTION_CHOICES, unique=True)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Contact Page Content'
        verbose_name_plural = 'Contact Page Contents'
        ordering = ['section']

    def __str__(self):
        return self.get_section_display()


class ContactInfo(models.Model):
    """Contact information (singleton pattern)"""
    phone = models.CharField(max_length=100, default='09455470173')
    email = models.EmailField(blank=True)
    address = models.TextField(default='Valencia, Negros Oriental, Philippines, 6215')
    city_country = models.CharField(max_length=200, default='Valencia, Negros Oriental, Philippines, 6215')
    google_maps_url = models.URLField(blank=True, max_length=1000, help_text="Google Maps directions URL")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Contact Information'
        verbose_name_plural = 'Contact Information'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    def __str__(self):
        return 'Contact Information'


class BusinessHour(models.Model):
    """Business hours for contact page"""
    day_range = models.CharField(max_length=100, help_text="e.g., 'Monday - Friday'")
    hours = models.CharField(max_length=100, help_text="e.g., '6:00 AM - 10:00 PM'")
    icon_color = models.CharField(max_length=50, default='primary', help_text="Bootstrap color name")
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order']
        verbose_name = 'Business Hour'
        verbose_name_plural = 'Business Hours'

    def __str__(self):
        return f"{self.day_range}: {self.hours}"


class ContactFAQ(models.Model):
    """FAQ items for contact page"""
    question = models.CharField(max_length=200)
    answer = models.TextField()
    icon_color = models.CharField(max_length=50, default='primary', help_text="Bootstrap color name")
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', '-created_at']
        verbose_name = 'Contact FAQ'
        verbose_name_plural = 'Contact FAQs'

    def __str__(self):
        return self.question


class SocialLink(models.Model):
    """Social media links for contact page"""
    platform = models.CharField(max_length=50, choices=[
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter'),
        ('instagram', 'Instagram'),
        ('whatsapp', 'WhatsApp'),
        ('linkedin', 'LinkedIn'),
        ('youtube', 'YouTube'),
        ('tiktok', 'TikTok'),
    ])
    url = models.URLField()
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'platform']
        verbose_name = 'Social Link'
        verbose_name_plural = 'Social Links'

    def __str__(self):
        return self.get_platform_display()

    @property
    def icon_class(self):
        icons = {
            'facebook': 'fab fa-facebook-f',
            'twitter': 'fab fa-twitter',
            'instagram': 'fab fa-instagram',
            'whatsapp': 'fab fa-whatsapp',
            'linkedin': 'fab fa-linkedin-in',
            'youtube': 'fab fa-youtube',
            'tiktok': 'fab fa-tiktok',
        }
        return icons.get(self.platform, 'fas fa-link')

    @property
    def button_class(self):
        classes = {
            'facebook': 'btn-outline-primary',
            'twitter': 'btn-outline-info',
            'instagram': 'btn-outline-danger',
            'whatsapp': 'btn-outline-success',
            'linkedin': 'btn-outline-primary',
            'youtube': 'btn-outline-danger',
            'tiktok': 'btn-outline-dark',
        }
        return classes.get(self.platform, 'btn-outline-secondary')


class Testimonial(models.Model):
    """Customer testimonials for the home page"""
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="The user who submitted this testimonial (if user-submitted)"
    )
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100, help_text="e.g., Regular Member, Tournament Player")
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=5,
        help_text="Rating from 1 to 5 stars"
    )
    text = models.TextField(help_text="Testimonial content")
    avatar = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(
        default=False,
        help_text="Only approved testimonials are displayed on the homepage"
    )
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', '-created_at']
        verbose_name = 'Testimonial'
        verbose_name_plural = 'Testimonials'

    def __str__(self):
        status = "✓" if self.is_approved else "⏳"
        return f"{status} {self.name} - {self.rating} stars"

    @property
    def status_display(self):
        if not self.is_approved:
            return "pending"
        return "approved" if self.is_active else "inactive"


class Rating(models.Model):
    """Rating submitted by users after reservation completion"""
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='ratings',
        help_text="The user who submitted this rating"
    )
    reservation = models.ForeignKey(
        'reservations.Reservation',
        on_delete=models.CASCADE,
        related_name='rating',
        help_text="The completed reservation being rated"
    )
    rating = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    comment = models.TextField(
        blank=True,
        null=True,
        max_length=500,
        help_text="Optional comment (max 500 characters)"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Featured ratings are displayed on the homepage"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Rating'
        verbose_name_plural = 'Ratings'
        unique_together = [['user', 'reservation']]

    def __str__(self):
        return f"{self.user.username} - {self.rating} stars for Reservation #{self.reservation.id}"

    @property
    def star_display(self):
        """Returns HTML for star display"""
        return '★' * self.rating + '☆' * (5 - self.rating)


class Amenity(models.Model):
    """Facility amenities displayed on home page"""
    icon = models.CharField(
        max_length=50,
        help_text="Font Awesome icon class, e.g., fa-wifi, fa-car",
        default="fa-check"
    )
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'title']
        verbose_name = 'Amenity'
        verbose_name_plural = 'Amenities'

    def __str__(self):
        return self.title


class GalleryImage(models.Model):
    """Gallery images for the home page"""
    image = models.ImageField(upload_to='gallery/')
    title = models.CharField(max_length=100, blank=True)
    alt_text = models.CharField(max_length=200, help_text="Alternative text for accessibility")
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', '-created_at']
        verbose_name = 'Gallery Image'
        verbose_name_plural = 'Gallery Images'

    def __str__(self):
        return self.title or f"Gallery Image {self.id}"

    @property
    def url(self):
        if self.image:
            return self.image.url
        return ''


class HomePageContent(models.Model):
    """Editable content sections for the home page"""
    SECTION_CHOICES = [
        ('hero_title', 'Hero Title'),
        ('hero_subtitle', 'Hero Subtitle'),
        ('about_title', 'About Section Title'),
        ('about_text', 'About Section Text'),
        ('cta_title', 'CTA Section Title'),
        ('cta_text', 'CTA Section Text'),
    ]
    
    section = models.CharField(max_length=50, choices=SECTION_CHOICES, unique=True)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Home Page Content'
        verbose_name_plural = 'Home Page Contents'

    def __str__(self):
        return self.get_section_display()


class ContactMessage(models.Model):
    """Contact form submissions from users"""
    SUBJECT_CHOICES = [
        ('general_inquiry', 'General Inquiry'),
        ('booking', 'Booking Related'),
        ('feedback', 'Feedback'),
        ('support', 'Technical Support'),
        ('partnership', 'Partnership'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('closed', 'Closed'),
    ]
    
    name = models.CharField(max_length=200)
    email = models.EmailField()
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES, default='general_inquiry')
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    admin_reply = models.TextField(blank=True, null=True, help_text="Admin's reply to this message")
    replied_at = models.DateTimeField(blank=True, null=True, help_text="When the admin replied")
    replied_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replied_messages',
        help_text="Admin user who replied"
    )
    is_read = models.BooleanField(default=False, help_text="Whether admin has read this message")
    user_read_reply = models.BooleanField(default=False, help_text="Whether user has read the admin's reply")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'

    def __str__(self):
        return f"{self.name} - {self.get_subject_display()} ({self.created_at.strftime('%Y-%m-%d')})"

    @property
    def status_badge_class(self):
        """Return Bootstrap badge class for status"""
        classes = {
            'new': 'bg-primary',
            'read': 'bg-info',
            'replied': 'bg-success',
            'closed': 'bg-secondary',
        }
        return classes.get(self.status, 'bg-secondary')


class AboutGalleryImage(models.Model):
    """Gallery images for the about page facility section"""
    image = models.ImageField(upload_to='about/gallery/')
    title = models.CharField(max_length=100, blank=True)
    alt_text = models.CharField(max_length=200, help_text="Alternative text for accessibility")
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', '-created_at']
        verbose_name = 'About Gallery Image'
        verbose_name_plural = 'About Gallery Images'
    def __str__(self):
        return self.title or f"About Gallery Image {self.id}"

    @property
    def url(self):
        if self.image:
            return self.image.url
        return ''


# ============================================================================
# COURTS PAGE CMS
# ============================================================================

class CourtPageSettings(models.Model):
    """Settings for the public courts page"""
    hero_title = models.CharField(max_length=200, default='Browse Courts')
    hero_subtitle = models.TextField(blank=True, default='Find the perfect court for your next game')
    page_title = models.CharField(max_length=200, blank=True, help_text='Browser tab title')
    meta_description = models.TextField(blank=True, help_text='SEO meta description')
    banner_image = models.ImageField(upload_to='cms/courts/', blank=True, null=True)
    show_search = models.BooleanField(default=True, help_text='Show/hide the search & filter bar')
    show_featured_first = models.BooleanField(default=True, help_text='Show featured courts before regular list')
    featured_title = models.CharField(max_length=200, blank=True, default='Featured Courts')
    featured_subtitle = models.TextField(blank=True, default='Handpicked courts you might love')
    promo_banner_title = models.CharField(max_length=200, blank=True)
    promo_banner_text = models.TextField(blank=True)
    promo_banner_link = models.URLField(blank=True)
    promo_banner_image = models.ImageField(upload_to='cms/courts/', blank=True, null=True)
    promo_banner_active = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Courts Page Setting'
        verbose_name_plural = 'Courts Page Settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    def __str__(self):
        return 'Courts Page Settings'


class FeaturedCourt(models.Model):
    """Featured court on the public courts page"""
    court = models.ForeignKey('courts.Court', on_delete=models.CASCADE, related_name='cms_features')
    label = models.CharField(max_length=100, blank=True, help_text='e.g. "Recommended", "Popular", "New"')
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', '-created_at']
        verbose_name = 'Featured Court'
        verbose_name_plural = 'Featured Courts'

    def __str__(self):
        return f"Featured: {self.court.name}"


# ============================================================================
# ORGANIZATIONS PAGE CMS
# ============================================================================

class OrganizationPageSettings(models.Model):
    """Settings for the public organizations page"""
    hero_title = models.CharField(max_length=200, default='Pickleball Organizations')
    hero_subtitle = models.TextField(blank=True, default='Discover pickleball organizations, courts, and tournaments near you')
    page_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    banner_image = models.ImageField(upload_to='cms/orgs/', blank=True, null=True)
    show_featured_first = models.BooleanField(default=True)
    featured_title = models.CharField(max_length=200, blank=True, default='Featured Organizations')
    featured_subtitle = models.TextField(blank=True, default='Top-rated organizations on our platform')
    show_verified_badge = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Organizations Page Setting'
        verbose_name_plural = 'Organizations Page Settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    def __str__(self):
        return 'Organizations Page Settings'


class OrganizationCategory(models.Model):
    """Categories for organizations"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fa-building')
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Organization Category'
        verbose_name_plural = 'Organization Categories'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class FeaturedOrganization(models.Model):
    """Featured organization on the public page"""
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name='cms_features')
    label = models.CharField(max_length=100, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', '-created_at']
        verbose_name = 'Featured Organization'
        verbose_name_plural = 'Featured Organizations'

    def __str__(self):
        return f"Featured: {self.organization.name}"


# ============================================================================
# TOURNAMENTS PAGE CMS
# ============================================================================

class TournamentPageSettings(models.Model):
    """Settings for the public tournaments page"""
    hero_title = models.CharField(max_length=200, default='Tournaments')
    hero_subtitle = models.TextField(blank=True, default='Join exciting pickleball competitions and showcase your skills')
    page_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    banner_image = models.ImageField(upload_to='cms/tournaments/', blank=True, null=True)
    announcement = models.TextField(blank=True, help_text='Global announcement shown at top of tournaments page')
    announcement_active = models.BooleanField(default=False)
    featured_title = models.CharField(max_length=200, blank=True, default='Featured Tournaments')
    featured_subtitle = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Tournaments Page Setting'
        verbose_name_plural = 'Tournaments Page Settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    def __str__(self):
        return 'Tournaments Page Settings'


class TournamentCategory(models.Model):
    """Categories for tournaments"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fa-trophy')
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Tournament Category'
        verbose_name_plural = 'Tournament Categories'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class FeaturedTournament(models.Model):
    """Featured tournament on the public page"""
    tournament = models.ForeignKey('tournaments.Tournament', on_delete=models.CASCADE, related_name='cms_features')
    label = models.CharField(max_length=100, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', '-created_at']
        verbose_name = 'Featured Tournament'
        verbose_name_plural = 'Featured Tournaments'

    def __str__(self):
        return f"Featured: {self.tournament.name}"


class TournamentAnnouncement(models.Model):
    """Individual tournament announcements"""
    title = models.CharField(max_length=200)
    message = models.TextField()
    link_url = models.URLField(blank=True, help_text='Optional link for more info')
    link_text = models.CharField(max_length=100, blank=True, default='Learn More')
    announcement_type = models.CharField(max_length=20, choices=[
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('danger', 'Urgent'),
    ], default='info')
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', '-created_at']
        verbose_name = 'Tournament Announcement'
        verbose_name_plural = 'Tournament Announcements'

    def __str__(self):
        return self.title


# ============================================================================
# EQUIPMENT PAGE CMS
# ============================================================================

class EquipmentPageSettings(models.Model):
    """Settings for the public equipment page"""
    hero_title = models.CharField(max_length=200, default='Equipment Rental')
    hero_subtitle = models.TextField(blank=True, default='Browse and rent quality equipment for your games')
    page_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    banner_image = models.ImageField(upload_to='cms/equipment/', blank=True, null=True)
    featured_title = models.CharField(max_length=200, blank=True, default='Featured Equipment')
    featured_subtitle = models.TextField(blank=True)
    show_availability_filter = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Equipment Page Setting'
        verbose_name_plural = 'Equipment Page Settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    def __str__(self):
        return 'Equipment Page Settings'


class EquipmentCategory(models.Model):
    """Categories for equipment"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fa-tools')
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Equipment Category'
        verbose_name_plural = 'Equipment Categories'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class FeaturedEquipment(models.Model):
    """Featured equipment item"""
    equipment = models.ForeignKey('equipment.Equipment', on_delete=models.CASCADE, related_name='cms_features')
    label = models.CharField(max_length=100, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', '-created_at']
        verbose_name = 'Featured Equipment'
        verbose_name_plural = 'Featured Equipment'

    def __str__(self):
        return f"Featured: {self.equipment.name}"


# ============================================================================
# MAINTENANCE MODE
# ============================================================================

class MaintenanceMode(models.Model):
    """Maintenance mode settings (singleton)"""
    is_active = models.BooleanField(default=False, help_text='Enable/disable maintenance mode')
    title = models.CharField(max_length=200, default='System Under Maintenance')
    message = models.TextField(default='We are performing scheduled maintenance. The system will be back shortly.')
    banner_image = models.ImageField(upload_to='cms/maintenance/', blank=True, null=True)
    estimated_return = models.DateTimeField(blank=True, null=True, help_text='Estimated time when system will be back')
    show_contact_info = models.BooleanField(default=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    scheduled_start = models.DateTimeField(blank=True, null=True, help_text='Scheduled maintenance start time')
    scheduled_end = models.DateTimeField(blank=True, null=True, help_text='Scheduled maintenance end time (auto-disables after this)')
    last_enabled_at = models.DateTimeField(blank=True, null=True)
    last_enabled_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='maintenance_enabled'
    )
    last_disabled_at = models.DateTimeField(blank=True, null=True)
    last_disabled_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='maintenance_disabled'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Maintenance Mode'
        verbose_name_plural = 'Maintenance Mode'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    def __str__(self):
        return f"Maintenance Mode: {'ON' if self.is_active else 'OFF'}"

    def clean(self):
        if self.scheduled_start and self.scheduled_end:
            if self.scheduled_start >= self.scheduled_end:
                raise ValidationError('Scheduled end time must be after start time.')


class MaintenanceAuditLog(models.Model):
    """Audit log for maintenance mode changes"""
    ACTION_CHOICES = [
        ('enabled', 'Maintenance Enabled'),
        ('disabled', 'Maintenance Disabled'),
        ('auto_disabled', 'Auto-Disabled (scheduled end)'),
        ('scheduled', 'Maintenance Scheduled'),
    ]
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Maintenance Audit Log'
        verbose_name_plural = 'Maintenance Audit Logs'

    def __str__(self):
        return f"{self.get_action_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


# ============================================================================
# SITE SETTINGS (Footer, Partners, Announcements)
# ============================================================================

class SiteSettings(models.Model):
    """Global site settings (singleton)"""
    # Footer
    footer_tagline = models.TextField(blank=True, default='The ultimate pickleball platform connecting players, courts, and organizations.')
    footer_email = models.EmailField(blank=True)
    footer_phone = models.CharField(max_length=50, blank=True)
    footer_address = models.TextField(blank=True)
    copyright_text = models.CharField(max_length=200, blank=True, default='© PickleSphere. All rights reserved.')
    
    # Statistics configuration (override auto-calculated values)
    override_stat_courts = models.IntegerField(blank=True, null=True, help_text='Override courts count (leave blank for auto)')
    override_stat_players = models.IntegerField(blank=True, null=True, help_text='Override players count')
    override_stat_organizations = models.IntegerField(blank=True, null=True, help_text='Override organizations count')
    override_stat_tournaments = models.IntegerField(blank=True, null=True, help_text='Override tournaments count')
    override_stat_years = models.IntegerField(blank=True, null=True, help_text='Override years operating')
    
    # Partners/Sponsors
    partners_title = models.CharField(max_length=200, blank=True, default='Our Partners')
    partners_subtitle = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site Setting'
        verbose_name_plural = 'Site Settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    def __str__(self):
        return 'Site Settings'


class Partner(models.Model):
    """Partner/Sponsor organizations"""
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='cms/partners/', blank=True, null=True)
    website_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = 'Partner'
        verbose_name_plural = 'Partners'

    def __str__(self):
        return self.name


class GlobalAnnouncement(models.Model):
    """Global announcements shown across the site"""
    title = models.CharField(max_length=200)
    message = models.TextField()
    announcement_type = models.CharField(max_length=20, choices=[
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('danger', 'Urgent'),
    ], default='info')
    link_url = models.URLField(blank=True)
    link_text = models.CharField(max_length=100, blank=True)
    show_on_pages = models.CharField(max_length=200, blank=True, help_text='Comma-separated page names, or leave blank for all pages')
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', '-created_at']
        verbose_name = 'Global Announcement'
        verbose_name_plural = 'Global Announcements'

    def __str__(self):
        return self.title


# ============================================================================
# CONTENT VERSION HISTORY
# ============================================================================

class ContentVersion(models.Model):
    """Track content version history for CMS items"""
    CONTENT_TYPE_CHOICES = [
        ('homepage', 'Home Page'),
        ('about', 'About Page'),
        ('contact', 'Contact Page'),
        ('pricing', 'Pricing Page'),
        ('courts', 'Courts Page'),
        ('organizations', 'Organizations Page'),
        ('tournaments', 'Tournaments Page'),
        ('equipment', 'Equipment Page'),
    ]
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    section = models.CharField(max_length=100, help_text='Which section/content was changed')
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    changed_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    version_number = models.PositiveIntegerField(help_text='Auto-incrementing version per content_type')
    is_published = models.BooleanField(default=True, help_text='Whether this version was published live')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Content Version'
        verbose_name_plural = 'Content Versions'
        indexes = [
            models.Index(fields=['content_type', '-version_number']),
        ]

    def __str__(self):
        return f"{self.get_content_type_display()} v{self.version_number} - {self.section}"
