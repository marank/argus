from django.contrib import admin

from apps.reservations.models import Handover, Reservation, ReservationItem


class ReservationItemInline(admin.TabularInline):
    model = ReservationItem
    extra = 0


class HandoverInline(admin.StackedInline):
    model = Handover
    extra = 0
    can_delete = False
    readonly_fields = [
        "method",
        "received_by",
        "received_by_name",
        "notes",
        "location",
        "handed_out_by",
        "handed_out_at",
    ]
    exclude = ["signature"]


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ["number", "title", "requester", "duration", "start_date", "status", "handover_mode"]
    list_filter = ["status", "duration", "handover_mode"]
    search_fields = ["number", "title", "requester__username", "requester__last_name"]
    autocomplete_fields = ["requester"]
    inlines = [ReservationItemInline, HandoverInline]
