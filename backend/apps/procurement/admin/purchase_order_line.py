from django.contrib import admin

from apps.procurement.models import PurchaseOrderLine


@admin.register(PurchaseOrderLine)
class PurchaseOrderLineAdmin(admin.ModelAdmin):
    list_display = ["order", "label", "quantity", "quantity_received", "unit_price", "asset_request_item"]
    list_filter = ["order__status"]
    search_fields = ["order__number", "description", "asset_model__name"]
    list_select_related = ["order", "asset_model__manufacturer", "asset_request_item__asset_request"]
    autocomplete_fields = ["order", "asset_model", "asset_request_item"]
