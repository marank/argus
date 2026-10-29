from typing import TYPE_CHECKING, TypedDict

from django.contrib import admin
from django.db.models import Count
from django.utils.translation import gettext_lazy as _

from apps.inventory.models import License, LicenseAssignment

if TYPE_CHECKING:
    from django_stubs_ext import WithAnnotations


class UsedSeats(TypedDict):
    used_seats: int


class LicenseAssignmentInline(admin.TabularInline):
    model = LicenseAssignment
    extra = 0
    fields = ["user", "asset", "note", "assigned_by", "created_at"]
    readonly_fields = ["assigned_by", "created_at"]
    autocomplete_fields = ["user", "asset"]


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ["model", "reference", "assign_to", "seats", "seats_used", "valid_until", "supplier"]
    list_filter = ["assign_to", "model__category", "model__manufacturer"]
    search_fields = ["model__name", "model__manufacturer__name", "reference", "license_key"]
    list_select_related = ["model__manufacturer", "supplier"]
    autocomplete_fields = ["model", "supplier"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "valid_until"
    inlines = [LicenseAssignmentInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(used_seats=Count("assignments"))

    @admin.display(description=_("seats used"), ordering="used_seats")
    def seats_used(self, obj: WithAnnotations[License, UsedSeats]) -> int:
        return obj.used_seats
