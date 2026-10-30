from django.contrib import admin

from apps.masterdata.models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin[Location]):
    list_display = ["full_name", "code", "kind", "is_pickup_point"]
    list_filter = ["kind", "is_pickup_point"]
    search_fields = ["name", "code", "parent__name"]
    list_select_related = ["parent__parent"]
    autocomplete_fields = ["parent"]
