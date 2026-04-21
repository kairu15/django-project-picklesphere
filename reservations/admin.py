from django.contrib import admin
from .models import Reservation, ReservationEquipment, CancellationRequest


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
    list_display = ['reservation', 'requested_by', 'approved', 'requested_at']
    list_filter = ['approved', 'requested_at']
