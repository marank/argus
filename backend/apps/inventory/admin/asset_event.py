from django.contrib import admin

from apps.inventory.models import AssetEvent


@admin.register(AssetEvent)
class AssetEventAdmin(admin.ModelAdmin):
    """Service log across all devices, e.g. every battery replacement."""

    list_display = ["occurred_at", "asset", "kind", "component", "cost", "performed_by", "related_user"]
    list_filter = ["kind", "asset__model__category", "asset__model"]
    search_fields = ["asset__inventory_number", "asset__serial_number", "description", "component"]
    list_select_related = ["asset__model__manufacturer", "performed_by", "related_user"]
    autocomplete_fields = ["asset", "performed_by", "related_user", "reservation"]
    date_hierarchy = "occurred_at"
    readonly_fields = ["created_at", "updated_at"]
