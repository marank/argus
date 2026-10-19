from django.contrib import admin

from apps.masterdata.models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "kind", "parent", "is_pickup_point"]
    search_fields = ["name", "code"]
