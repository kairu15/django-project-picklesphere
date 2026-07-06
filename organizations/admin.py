from django.contrib import admin
from .models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'is_active', 'court_count', 'staff_count', 'created_at']
    list_filter = ['status', 'is_active']
    search_fields = ['name', 'contact_email', 'contact_phone']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at', 'approved_at']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'slug', 'description', 'logo', 'banner']
        }),
        ('Contact & Location', {
            'fields': ['address', 'city', 'province', 'contact_email', 'contact_phone', 'website']
        }),
        ('Status & Approval', {
            'fields': ['status', 'is_active', 'registration_notes', 'approved_by', 'approved_at', 'rejection_reason']
        }),
        ('Settings', {
            'fields': ['max_staff_accounts']
        }),
        ('Metadata', {
            'fields': ['created_at', 'updated_at']
        }),
    ]
