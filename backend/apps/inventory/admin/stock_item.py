from django.contrib import admin

from apps.inventory.models import StockItem, StockMovement


class StockMovementInline(admin.TabularInline):
    model = StockMovement
    extra = 0
    fields = ["created_at", "delta", "reason", "note", "performed_by", "recipient"]
    readonly_fields = ["created_at"]


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ["model", "location", "quantity", "reserved_quantity", "min_quantity"]
    list_filter = ["location", "model__category"]
    inlines = [StockMovementInline]
