from django.contrib import admin

from apps.inventory.models import Asset, AssetEvent


class AssetEventInline(admin.TabularInline):
    model = AssetEvent
    fk_name = "asset"
    extra = 0
    fields = ["occurred_at", "kind", "description", "component", "performed_by", "related_user"]
    autocomplete_fields = ["performed_by", "related_user"]


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ["inventory_number", "model", "serial_number", "status", "assigned_to"]
    list_filter = ["status", "condition", "model__category", "is_loanable"]
    search_fields = ["inventory_number", "serial_number", "imei", "hostname"]
    autocomplete_fields = ["assigned_to", "parent"]
    inlines = [AssetEventInline]
