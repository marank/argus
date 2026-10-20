from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.reservations.models import Handover, Reservation, ReservationItem


class ReservationItemInline(admin.TabularInline):
    model = ReservationItem
    extra = 0
    fields = [
        "position",
        "category",
        "asset_model",
        "description",
        "quantity_requested",
        "quantity_confirmed",
        "note",
    ]
    autocomplete_fields = ["category", "asset_model"]
    show_change_link = True


class HandoverInline(admin.StackedInline):
    model = Handover
    extra = 0
    can_delete = False
    fields = [
        "method",
        "received_by",
        "received_by_name",
        "location",
        "notes",
        "handed_out_by",
        "handed_out_at",
        "signature_preview",
    ]
    readonly_fields = fields

    def has_add_permission(self, request, obj=None) -> bool:
        return False

    @admin.display(description=_("signature"))
    def signature_preview(self, obj: Handover):
        from .handover import signature_image

        return signature_image(obj)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = [
        "number",
        "title",
        "requester",
        "duration",
        "start_date",
        "end_date",
        "status",
        "handover_mode",
        "pickup_at",
        "assigned_team",
        "assignee",
    ]
    list_filter = ["status", "duration", "handover_mode", "requester__department", "assigned_team"]
    search_fields = ["number", "title", "requester__username", "requester__last_name"]
    list_select_related = ["requester", "assigned_team", "assignee"]
    autocomplete_fields = [
        "requester",
        "created_by",
        "handled_by",
        "prepared_by",
        "pickup_location",
        "assigned_team",
        "assignee",
    ]
    date_hierarchy = "start_date"
    readonly_fields = [
        "number",
        "confirmed_at",
        "handed_out_at",
        "reminded_at",
        "reminded_by",
        "completed_at",
        "created_at",
        "updated_at",
    ]
    fieldsets = [
        (None, {"fields": ["number", "title", "requester", "created_by", "status"]}),
        (_("Period"), {"fields": ["duration", "start_date", "end_date"]}),
        (_("Pickup"), {"fields": ["handover_mode", "pickup_at", "pickup_location"]}),
        (_("Responsible"), {"fields": ["assigned_team", "assignee"]}),
        (_("Notes"), {"fields": ["notes", "it_comment", "handled_by", "prepared_by"]}),
        (
            _("History"),
            {
                "fields": [
                    "confirmed_at",
                    "handed_out_at",
                    "reminded_at",
                    "reminded_by",
                    "completed_at",
                    "created_at",
                    "updated_at",
                ],
                "classes": ["collapse"],
            },
        ),
    ]
    inlines = [ReservationItemInline, HandoverInline]
