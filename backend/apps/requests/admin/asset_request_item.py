from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.requests.models import AssetRequestAllocation, AssetRequestItem


class AllocationInline(admin.TabularInline[AssetRequestAllocation, AssetRequestItem]):
    model = AssetRequestAllocation
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


@admin.register(AssetRequestItem)
class AssetRequestItemAdmin(admin.ModelAdmin[AssetRequestItem]):
    list_display = ["asset_request", "label", "quantity_requested", "quantity_confirmed", "is_free_text"]
    list_filter = ["asset_request__status", "category"]
    search_fields = ["asset_request__number", "description", "asset_model__name", "category__name"]
    list_select_related = ["asset_request", "category", "asset_model__manufacturer"]
    autocomplete_fields = ["asset_request", "category", "asset_model"]
    inlines = [AllocationInline]

    @admin.display(boolean=True, description=_("custom request"))
    def is_free_text(self, obj: AssetRequestItem) -> bool:
        return obj.is_free_text
