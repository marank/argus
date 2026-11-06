from django.contrib import admin

from apps.masterdata.models import ComponentType


@admin.register(ComponentType)
class ComponentTypeAdmin(admin.ModelAdmin[ComponentType]):
    list_display = ["name", "sort_order"]
    list_editable = ["sort_order"]
    search_fields = ["name"]
    filter_horizontal = ["categories"]
