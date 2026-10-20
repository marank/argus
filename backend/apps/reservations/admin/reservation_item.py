from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.reservations.models import ReservationAllocation, ReservationItem


class AllocationInline(admin.TabularInline):
    model = ReservationAllocation
    extra = 0
    fields = [
        "asset",
        "consumable",
        "license",
        "quantity",
        "allocated_by",
        "allocated_at",
        "handout_note",
        "handed_out_at",
        "returned_at",
        "return_note",
    ]
    readonly_fields = ["allocated_at"]
    raw_id_fields = ["license"]
    autocomplete_fields = ["asset", "consumable", "allocated_by"]


@admin.register(ReservationItem)
class ReservationItemAdmin(admin.ModelAdmin):
    list_display = ["reservation", "label", "quantity_requested", "quantity_confirmed", "is_free_text"]
    list_filter = ["reservation__status", "category"]
    search_fields = ["reservation__number", "description", "asset_model__name", "category__name"]
    list_select_related = ["reservation", "category", "asset_model__manufacturer"]
    autocomplete_fields = ["reservation", "category", "asset_model"]
    inlines = [AllocationInline]

    @admin.display(boolean=True, description=_("custom request"))
    def is_free_text(self, obj: ReservationItem) -> bool:
        return obj.is_free_text
