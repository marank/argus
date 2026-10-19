from django.contrib import admin

from apps.masterdata.models import AssetModel


@admin.register(AssetModel)
class AssetModelAdmin(admin.ModelAdmin):
    list_display = ["name", "manufacturer", "category", "tracking", "ean", "is_active"]
    list_filter = ["tracking", "category", "manufacturer"]
    search_fields = ["name", "part_number", "ean"]
    filter_horizontal = ["compatible_with"]
