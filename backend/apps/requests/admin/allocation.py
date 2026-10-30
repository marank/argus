from django.contrib import admin

from apps.requests.models import AssetRequestAllocation


@admin.register(AssetRequestAllocation)
class AssetRequestAllocationAdmin(admin.ModelAdmin[AssetRequestAllocation]):
    list_display = [
        "item",
        "asset",
        "consumable",
        "license",
        "quantity",
        "allocated_at",
        "handed_out_at",
        "returned_at",
    ]
    list_filter = ["item__asset_request__status"]
    search_fields = ["item__asset_request__number", "asset__inventory_number", "asset__serial_number"]
    list_select_related = ["item__asset_request", "asset__model", "consumable__model"]
    autocomplete_fields = ["item", "asset", "consumable", "allocated_by"]
    raw_id_fields = ["license", "license_assignment", "device_return"]
    readonly_fields = ["allocated_at"]
