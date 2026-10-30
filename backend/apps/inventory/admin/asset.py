from django.contrib import admin
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from apps.inventory.models import Asset, AssetEvent


class AssetEventInline(admin.TabularInline[AssetEvent, Asset]):
    model = AssetEvent
    fk_name = "asset"
    extra = 0
    fields = ["occurred_at", "kind", "description", "component", "cost", "performed_by", "related_user"]
    autocomplete_fields = ["performed_by", "related_user"]
    ordering = ["-occurred_at"]


class ComponentInline(admin.TabularInline[Asset, Asset]):
    model = Asset
    fk_name = "parent"
    extra = 0
    fields = ("inventory_number", "model", "serial_number", "status")
    readonly_fields = fields
    can_delete = False
    show_change_link = True
    verbose_name = _("attached device")
    verbose_name_plural = _("attached devices")

    def has_add_permission(self, request: HttpRequest, obj: Asset | None = None) -> bool:
        return False


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin[Asset]):
    list_display = [
        "inventory_number",
        "model",
        "serial_number",
        "status",
        "condition",
        "assigned_to",
        "location",
        "warranty_until",
    ]
    list_filter = ["status", "condition", "is_loanable", "model__category", "model__manufacturer", "location"]
    search_fields = [
        "inventory_number",
        "serial_number",
        "imei",
        "mac_address",
        "hostname",
        "model__name",
        "assigned_to__username",
        "assigned_to__last_name",
    ]
    list_select_related = ["model__manufacturer", "assigned_to", "location"]
    autocomplete_fields = [
        "model",
        "location",
        "assigned_to",
        "parent",
        "supplier",
        "purchase_order_line",
        "consumables",
    ]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "purchase_date"
    fieldsets = [
        (None, {"fields": ["inventory_number", "model", "serial_number", "imei", "mac_address", "hostname"]}),
        (
            _("Status & usage"),
            {
                "fields": [
                    "status",
                    "condition",
                    "is_loanable",
                    "location",
                    "assigned_to",
                    "assigned_since",
                    "parent",
                ]
            },
        ),
        (
            _("Purchase & warranty"),
            {
                "fields": [
                    "supplier",
                    "purchase_order_line",
                    "purchase_date",
                    "purchase_price",
                    "warranty_until",
                ]
            },
        ),
        (_("Consumables"), {"fields": ["consumables"]}),
        (_("Notes"), {"fields": ["notes"]}),
        (_("History"), {"fields": ["created_at", "updated_at"], "classes": ["collapse"]}),
    ]
    inlines = [ComponentInline, AssetEventInline]
