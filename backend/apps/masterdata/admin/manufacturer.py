from django.contrib import admin

from apps.masterdata.models import Manufacturer


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ["name", "website", "support_phone", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "website"]
