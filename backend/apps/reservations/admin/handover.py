from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.reservations.models import Handover


def signature_image(obj: Handover):
    if not obj.signature:
        return "—"
    return format_html(
        '<img src="{}" alt="" style="height:90px;background:#fff;border:1px solid #ccc;padding:4px">',
        obj.signature,
    )


@admin.register(Handover)
class HandoverAdmin(admin.ModelAdmin):
    """Handover records are evidence: viewable, not editable."""

    list_display = ["reservation", "method", "received_by_name", "handed_out_by", "handed_out_at"]
    list_filter = ["method"]
    search_fields = ["reservation__number", "received_by_name", "received_by__last_name"]
    list_select_related = ["reservation", "handed_out_by"]
    date_hierarchy = "handed_out_at"
    exclude = ["signature"]
    readonly_fields = [
        "reservation",
        "method",
        "received_by",
        "received_by_name",
        "location",
        "notes",
        "handed_out_by",
        "recorded_by",
        "handed_out_at",
        "signature_preview",
    ]

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    @admin.display(description=_("signature"))
    def signature_preview(self, obj: Handover):
        return signature_image(obj)
