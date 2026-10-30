from django.contrib import admin
from django.http import HttpRequest

from apps.inventory.models import AssetIssue, AssetIssueEntry


class AssetIssueEntryInline(admin.TabularInline[AssetIssueEntry, AssetIssue]):
    model = AssetIssueEntry
    extra = 0
    fields = ("created_at", "kind", "author", "text", "status")
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request: HttpRequest, obj: AssetIssue | None = None) -> bool:
        # Written in the app, which also notifies the other side.
        return False


@admin.register(AssetIssue)
class AssetIssueAdmin(admin.ModelAdmin[AssetIssue]):
    list_display = [
        "created_at",
        "asset",
        "kind",
        "status",
        "reported_by",
        "assigned_team",
        "assignee",
    ]
    list_filter = ["status", "kind", "assigned_team"]
    search_fields = ["asset__inventory_number", "description", "reported_by__last_name"]
    list_select_related = [
        "asset__model__manufacturer",
        "reported_by",
        "assigned_team",
        "assignee",
    ]
    autocomplete_fields = ["asset", "reported_by", "handled_by", "assigned_team", "assignee"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"
    inlines = [AssetIssueEntryInline]
