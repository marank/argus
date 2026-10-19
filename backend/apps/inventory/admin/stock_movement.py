from django.contrib import admin

from apps.inventory.models import StockMovement


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    """Read-only journal; movements are booked through the app."""

    list_display = ["created_at", "stock_item", "delta", "reason", "performed_by", "recipient", "note"]
    list_filter = ["reason", "stock_item__location", "stock_item__model__category"]
    search_fields = ["stock_item__model__name", "note", "recipient__last_name"]
    list_select_related = [
        "stock_item__model__manufacturer",
        "stock_item__location",
        "performed_by",
        "recipient",
    ]
    date_hierarchy = "created_at"

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False
