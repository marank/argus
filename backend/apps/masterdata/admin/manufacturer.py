from django.contrib import admin

from apps.masterdata.models import Manufacturer


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ["name", "website", "is_active"]
    search_fields = ["name"]
