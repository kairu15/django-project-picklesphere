from django.contrib import admin
from .models import Reservation, ReservationEquipment, CancellationRequest, CancellationPolicy


class ReservationEquipmentInline(admin.TabularInline):
    model = ReservationEquipment
    extra = 0


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'court', 'date', 'start_time', 'end_time', 'status', 'total_amount']
    list_filter = ['status', 'date', 'court__site']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'court__name']
    date_hierarchy = 'date'
    inlines = [ReservationEquipmentInline]


@admin.register(CancellationRequest)
class CancellationRequestAdmin(admin.ModelAdmin):
    list_display = ['reservation', 'requested_by', 'approved', 'deduction_percentage', 'deduction_amount', 'is_within_time_limit', 'requested_at']
    list_filter = ['approved', 'is_within_time_limit', 'requested_at']
    readonly_fields = ['deduction_amount', 'deduction_percentage', 'cancellation_note', 'is_within_time_limit']
    fieldsets = (
        ('Reservation Information', {
            'fields': ('reservation', 'requested_by', 'requested_at')
        }),
        ('Cancellation Details', {
            'fields': ('reason', 'approved', 'approved_by', 'approved_at')
        }),
        ('Refund Information', {
            'fields': ('refund_method', 'gcash_number', 'account_name', 'paypal_email', 'refund_processed', 'refund_processed_at')
        }),
        ('Cancellation Policy', {
            'fields': ('is_within_time_limit', 'deduction_percentage', 'deduction_amount', 'cancellation_note'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CancellationPolicy)
class CancellationPolicyAdmin(admin.ModelAdmin):
    list_display = ['name', 'time_limit_minutes', 'deduction_percentage', 'is_active', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    fieldsets = (
        ('Policy Settings', {
            'fields': ('name', 'time_limit_minutes', 'deduction_percentage', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
