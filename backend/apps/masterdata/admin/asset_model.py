from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.masterdata.models import AssetModel


@admin.register(AssetModel)
class AssetModelAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "manufacturer",
        "category",
        "tracking",
        "ean",
        "list_price",
        "is_requestable",
        "is_active",
    ]
    list_filter = ["tracking", "is_active", "is_requestable", "category", "manufacturer"]
    search_fields = ["name", "part_number", "ean", "manufacturer__name"]
    list_select_related = ["manufacturer", "category"]
    autocomplete_fields = ["manufacturer", "category", "default_supplier", "compatible_with"]
    fieldsets = [
        (None, {"fields": ["name", "manufacturer", "category", "tracking"]}),
        (_("Identification"), {"fields": ["part_number", "ean"]}),
        (_("Procurement"), {"fields": ["default_supplier", "list_price", "warranty_months"]}),
        (_("Employee portal"), {"fields": ["is_requestable", "is_active"]}),
        (_("Details"), {"fields": ["compatible_with", "description", "specifications"]}),
    ]
