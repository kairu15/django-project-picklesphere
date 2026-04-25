from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Testimonial(models.Model):
    """Customer testimonials for the home page"""
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
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', '-created_at']
        verbose_name = 'Testimonial'
        verbose_name_plural = 'Testimonials'

    def __str__(self):
        return f"{self.name} - {self.rating} stars"


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
