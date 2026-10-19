from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.procurement.models import PurchaseOrder, PurchaseOrderLine


class PurchaseOrderLineInline(admin.TabularInline):
    model = PurchaseOrderLine
    extra = 0
    fields = [
        "position",
        "asset_model",
        "description",
        "quantity",
        "unit_price",
        "quantity_received",
        "reservation_item",
    ]
    autocomplete_fields = ["asset_model", "reservation_item"]


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = [
        "number",
        "supplier",
        "status",
        "order_date",
        "expected_date",
        "supplier_reference",
        "order_total",
    ]
    list_filter = ["status", "supplier"]
    search_fields = ["number", "supplier_reference", "supplier__name"]
    list_select_related = ["supplier"]
    autocomplete_fields = ["supplier", "delivery_location", "created_by"]
    date_hierarchy = "order_date"
    readonly_fields = ["number", "created_at", "updated_at"]
    inlines = [PurchaseOrderLineInline]

    @admin.display(description=_("total"))
    def order_total(self, obj: PurchaseOrder):
        return obj.total
