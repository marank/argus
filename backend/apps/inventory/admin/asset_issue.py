from django.contrib import admin

from apps.inventory.models import AssetIssue


@admin.register(AssetIssue)
class AssetIssueAdmin(admin.ModelAdmin):
    list_display = ["created_at", "asset", "kind", "status", "reported_by", "handled_by"]
    list_filter = ["status", "kind"]
    search_fields = ["asset__inventory_number", "description", "reported_by__last_name"]
    list_select_related = ["asset__model__manufacturer", "reported_by", "handled_by"]
    autocomplete_fields = ["asset", "reported_by", "handled_by"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"
