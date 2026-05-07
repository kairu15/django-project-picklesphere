from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


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
