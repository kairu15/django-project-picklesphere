from django.contrib import admin
from .models import Testimonial, Amenity, GalleryImage, HomePageContent


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
    
    def icon_preview(self, obj):
        return f'<i class="fas {obj.icon}"></i> {obj.icon}'
    icon_preview.allow_tags = True


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
