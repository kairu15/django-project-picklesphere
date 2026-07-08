from django.contrib import admin
from .models import (
    Testimonial, Rating, Amenity, GalleryImage, HomePageContent,
    PricingContent, PricingTier, PricingFAQ,
    AboutContent, Milestone, TeamMember, Facility, WhyChooseItem,
    ContactContent, ContactInfo, BusinessHour, ContactFAQ, SocialLink,
    # CMS Models
    CourtPageSettings, FeaturedCourt,
    OrganizationPageSettings, OrganizationCategory, FeaturedOrganization,
    TournamentPageSettings, TournamentCategory, FeaturedTournament, TournamentAnnouncement,
    EquipmentPageSettings, EquipmentCategory, FeaturedEquipment,
    MaintenanceMode, MaintenanceAuditLog,
    SiteSettings, Partner, GlobalAnnouncement,
    ContentVersion,
)


# Pricing Admin Classes
@admin.register(PricingContent)
class PricingContentAdmin(admin.ModelAdmin):
    list_display = ['section', 'content_short', 'is_active', 'updated_at']
    list_filter = ['is_active', 'section']
    search_fields = ['section', 'content']
    list_editable = ['is_active']
    fields = ['section', 'content', 'is_active']
    readonly_fields = ['updated_at']

    def content_short(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_short.short_description = 'Content Preview'


@admin.register(PricingTier)
class PricingTierAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'period', 'is_recommended', 'is_active', 'display_order']
    list_filter = ['is_active', 'is_recommended']
    search_fields = ['name', 'description']
    ordering = ['display_order', 'price']
    list_editable = ['is_active', 'is_recommended', 'display_order', 'price']
    fields = ['name', 'price', 'period', 'description', 'features', 'is_recommended', 'is_active', 'display_order']


@admin.register(PricingFAQ)
class PricingFAQAdmin(admin.ModelAdmin):
    list_display = ['question_short', 'is_active', 'display_order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['question', 'answer']
    ordering = ['display_order', '-created_at']
    list_editable = ['is_active', 'display_order']
    fields = ['question', 'answer', 'is_active', 'display_order']

    def question_short(self, obj):
        return obj.question[:80] + '...' if len(obj.question) > 80 else obj.question
    question_short.short_description = 'Question'


# About Admin Classes
@admin.register(AboutContent)
class AboutContentAdmin(admin.ModelAdmin):
    list_display = ['section', 'content_short', 'is_active', 'updated_at']
    list_filter = ['is_active', 'section']
    search_fields = ['section', 'content']
    list_editable = ['is_active']
    fields = ['section', 'content', 'is_active']
    readonly_fields = ['updated_at']

    def content_short(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_short.short_description = 'Content Preview'


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ['year', 'title', 'color', 'is_active', 'display_order']
    list_filter = ['is_active', 'color']
    search_fields = ['year', 'title', 'description']
    ordering = ['display_order', 'year']
    list_editable = ['is_active', 'color', 'display_order']
    fields = ['year', 'title', 'description', 'color', 'is_active', 'display_order']


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'color', 'is_active', 'display_order', 'photo_preview']
    list_filter = ['is_active', 'color']
    search_fields = ['name', 'role', 'bio']
    ordering = ['display_order', 'name']
    list_editable = ['is_active', 'display_order']
    fields = ['name', 'role', 'bio', 'photo', 'linkedin_url', 'twitter_url', 'color', 'is_active', 'display_order']

    def photo_preview(self, obj):
        if obj.photo:
            return f'<img src="{obj.photo.url}" style="max-height: 50px; max-width: 50px; border-radius: 50%;" />'
        return '<div style="width: 50px; height: 50px; background: #ddd; border-radius: 50%; display: flex; align-items: center; justify-content: center;"><i class="fas fa-user"></i></div>'
    photo_preview.allow_tags = True
    photo_preview.short_description = 'Photo'


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ['title', 'icon', 'color', 'is_active', 'display_order']
    list_filter = ['is_active', 'color']
    search_fields = ['title', 'description']
    ordering = ['display_order', 'title']
    list_editable = ['is_active', 'icon', 'color', 'display_order']
    fields = ['icon', 'title', 'description', 'color', 'is_active', 'display_order']


@admin.register(WhyChooseItem)
class WhyChooseItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'icon', 'color', 'is_active', 'display_order']
    list_filter = ['is_active', 'color']
    search_fields = ['title', 'description']
    ordering = ['display_order', 'title']
    list_editable = ['is_active', 'icon', 'color', 'display_order']
    fields = ['icon', 'title', 'description', 'color', 'is_active', 'display_order']


# Contact Admin Classes
@admin.register(ContactContent)
class ContactContentAdmin(admin.ModelAdmin):
    list_display = ['section', 'content_short', 'is_active', 'updated_at']
    list_filter = ['is_active', 'section']
    search_fields = ['section', 'content']
    list_editable = ['is_active']
    fields = ['section', 'content', 'is_active']
    readonly_fields = ['updated_at']

    def content_short(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_short.short_description = 'Content Preview'


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ['phone', 'email', 'address_short', 'updated_at']
    fields = ['phone', 'email', 'address', 'city_country', 'google_maps_url']
    readonly_fields = ['updated_at']

    def address_short(self, obj):
        return obj.address[:50] + '...' if len(obj.address) > 50 else obj.address
    address_short.short_description = 'Address'

    def has_add_permission(self, request):
        # Only allow one instance
        return not ContactInfo.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BusinessHour)
class BusinessHourAdmin(admin.ModelAdmin):
    list_display = ['day_range', 'hours', 'icon_color', 'is_active', 'display_order']
    list_filter = ['is_active', 'icon_color']
    ordering = ['display_order']
    list_editable = ['is_active', 'icon_color', 'hours', 'display_order']
    fields = ['day_range', 'hours', 'icon_color', 'is_active', 'display_order']


@admin.register(ContactFAQ)
class ContactFAQAdmin(admin.ModelAdmin):
    list_display = ['question_short', 'icon_color', 'is_active', 'display_order', 'created_at']
    list_filter = ['is_active', 'icon_color', 'created_at']
    search_fields = ['question', 'answer']
    ordering = ['display_order', '-created_at']
    list_editable = ['is_active', 'icon_color', 'display_order']
    fields = ['question', 'answer', 'icon_color', 'is_active', 'display_order']

    def question_short(self, obj):
        return obj.question[:80] + '...' if len(obj.question) > 80 else obj.question
    question_short.short_description = 'Question'


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ['platform', 'url_short', 'is_active', 'display_order']
    list_filter = ['is_active', 'platform']
    ordering = ['display_order', 'platform']
    list_editable = ['is_active', 'display_order']
    fields = ['platform', 'url', 'is_active', 'display_order']

    def url_short(self, obj):
        return obj.url[:50] + '...' if len(obj.url) > 50 else obj.url
    url_short.short_description = 'URL'


# Homepage Admin Classes (existing)
@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'reservation', 'rating', 'comment_short', 'is_featured', 'created_at']
    list_filter = ['is_featured', 'rating', 'created_at']
    list_editable = ['is_featured']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'comment']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    fields = ['user', 'reservation', 'rating', 'comment', 'is_featured', 'created_at', 'updated_at']

    def comment_short(self, obj):
        if obj.comment:
            return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
        return '-'
    comment_short.short_description = 'Comment'


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'rating', 'is_active', 'display_order', 'created_at']
    list_filter = ['is_active', 'rating', 'created_at']
    search_fields = ['name', 'role', 'text']
    ordering = ['display_order', '-created_at']
    list_editable = ['is_active', 'display_order', 'rating']
    fields = ['name', 'role', 'rating', 'text', 'avatar', 'is_active', 'display_order']


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ['title', 'icon', 'is_active', 'display_order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['display_order', 'title']
    list_editable = ['is_active', 'display_order']
    fields = ['icon', 'title', 'description', 'is_active', 'display_order']


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'alt_text', 'is_active', 'display_order', 'created_at', 'image_preview']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'alt_text']
    ordering = ['display_order', '-created_at']
    list_editable = ['is_active', 'display_order', 'title', 'alt_text']
    fields = ['image', 'title', 'alt_text', 'is_active', 'display_order']

    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 50px; max-width: 100px;" />'
        return 'No image'
    image_preview.allow_tags = True
    image_preview.short_description = 'Preview'


@admin.register(HomePageContent)
class HomePageContentAdmin(admin.ModelAdmin):
    list_display = ['section', 'is_active', 'updated_at']
    list_filter = ['is_active', 'section']
    search_fields = ['section', 'content']
    list_editable = ['is_active']
    fields = ['section', 'content', 'is_active']
    readonly_fields = ['updated_at']


# ============================================================================
# CMS Admin Registrations
# ============================================================================

@admin.register(CourtPageSettings)
class CourtPageSettingsAdmin(admin.ModelAdmin):
    list_display = ['hero_title', 'show_search', 'show_featured_first', 'is_active', 'updated_at']
    fieldsets = [
        ('Hero Section', {'fields': ['hero_title', 'hero_subtitle', 'banner_image']}),
        ('SEO', {'fields': ['page_title', 'meta_description']}),
        ('Settings', {'fields': ['show_search', 'show_featured_first', 'is_active']}),
        ('Featured Section', {'fields': ['featured_title', 'featured_subtitle']}),
        ('Promo Banner', {'fields': ['promo_banner_title', 'promo_banner_text', 'promo_banner_link', 'promo_banner_image', 'promo_banner_active']}),
    ]
    readonly_fields = ['updated_at']


@admin.register(FeaturedCourt)
class FeaturedCourtAdmin(admin.ModelAdmin):
    list_display = ['court', 'label', 'display_order', 'is_active']
    list_editable = ['display_order', 'is_active', 'label']
    list_filter = ['is_active']
    search_fields = ['court__name']


@admin.register(OrganizationPageSettings)
class OrganizationPageSettingsAdmin(admin.ModelAdmin):
    list_display = ['hero_title', 'show_featured_first', 'show_verified_badge', 'is_active']
    readonly_fields = ['updated_at']


@admin.register(OrganizationCategory)
class OrganizationCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'display_order', 'is_active']
    list_editable = ['display_order', 'is_active']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(FeaturedOrganization)
class FeaturedOrganizationAdmin(admin.ModelAdmin):
    list_display = ['organization', 'label', 'display_order', 'is_active']
    list_editable = ['display_order', 'is_active']


@admin.register(TournamentPageSettings)
class TournamentPageSettingsAdmin(admin.ModelAdmin):
    list_display = ['hero_title', 'announcement_active', 'is_active']
    readonly_fields = ['updated_at']


@admin.register(TournamentCategory)
class TournamentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'display_order', 'is_active']
    list_editable = ['display_order', 'is_active']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(FeaturedTournament)
class FeaturedTournamentAdmin(admin.ModelAdmin):
    list_display = ['tournament', 'label', 'display_order', 'is_active']
    list_editable = ['display_order', 'is_active']


@admin.register(TournamentAnnouncement)
class TournamentAnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'announcement_type', 'is_active', 'display_order']
    list_editable = ['is_active', 'display_order']
    list_filter = ['announcement_type', 'is_active']


@admin.register(EquipmentPageSettings)
class EquipmentPageSettingsAdmin(admin.ModelAdmin):
    list_display = ['hero_title', 'show_availability_filter', 'is_active']
    readonly_fields = ['updated_at']


@admin.register(EquipmentCategory)
class EquipmentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'display_order', 'is_active']
    list_editable = ['display_order', 'is_active']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(FeaturedEquipment)
class FeaturedEquipmentAdmin(admin.ModelAdmin):
    list_display = ['equipment', 'label', 'display_order', 'is_active']
    list_editable = ['display_order', 'is_active']


@admin.register(MaintenanceMode)
class MaintenanceModeAdmin(admin.ModelAdmin):
    list_display = ['is_active', 'title', 'estimated_return', 'scheduled_start', 'scheduled_end']
    readonly_fields = ['last_enabled_at', 'last_disabled_at', 'last_enabled_by', 'last_disabled_by', 'updated_at']

    def has_add_permission(self, request):
        return not MaintenanceMode.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MaintenanceAuditLog)
class MaintenanceAuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'performed_by', 'created_at']
    list_filter = ['action', 'created_at']
    readonly_fields = ['action', 'performed_by', 'details', 'ip_address', 'created_at']
    search_fields = ['details']


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['footer_email', 'copyright_text', 'is_active']
    readonly_fields = ['updated_at']

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'website_url', 'display_order', 'is_active']
    list_editable = ['display_order', 'is_active']
    search_fields = ['name']


@admin.register(GlobalAnnouncement)
class GlobalAnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'announcement_type', 'is_active', 'display_order', 'created_at']
    list_editable = ['is_active', 'display_order']
    list_filter = ['announcement_type', 'is_active']


@admin.register(ContentVersion)
class ContentVersionAdmin(admin.ModelAdmin):
    list_display = ['content_type', 'section', 'version_number', 'is_published', 'changed_by', 'created_at']
    list_filter = ['content_type', 'is_published', 'created_at']
    readonly_fields = ['content_type', 'section', 'old_value', 'new_value', 'changed_by', 'version_number', 'is_published', 'created_at']
    search_fields = ['section']
