from django.contrib import admin

from apps.procurement.models import PurchaseOrder, PurchaseOrderLine


class PurchaseOrderLineInline(admin.TabularInline):
    model = PurchaseOrderLine
    extra = 0


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ["number", "supplier", "status", "order_date", "expected_date"]
    list_filter = ["status", "supplier"]
    search_fields = ["number", "supplier_reference"]
    inlines = [PurchaseOrderLineInline]
