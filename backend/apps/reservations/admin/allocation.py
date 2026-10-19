from django.contrib import admin

from apps.reservations.models import ReservationAllocation


@admin.register(ReservationAllocation)
class ReservationAllocationAdmin(admin.ModelAdmin):
    list_display = ["item", "asset", "consumable", "quantity", "allocated_at", "handed_out_at", "returned_at"]
    list_filter = ["item__reservation__status"]
    search_fields = ["item__reservation__number", "asset__inventory_number", "asset__serial_number"]
    list_select_related = ["item__reservation", "asset__model", "consumable__model"]
    autocomplete_fields = ["item", "asset", "consumable", "allocated_by"]
    readonly_fields = ["allocated_at"]
