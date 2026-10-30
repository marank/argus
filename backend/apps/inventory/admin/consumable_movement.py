from django.contrib import admin
from django.http import HttpRequest

from apps.inventory.models import ConsumableMovement


@admin.register(ConsumableMovement)
class ConsumableMovementAdmin(admin.ModelAdmin[ConsumableMovement]):
    """Read-only journal; movements are booked through the app."""

    list_display = ["created_at", "consumable", "delta", "reason", "performed_by", "recipient", "note"]
    list_filter = ["reason", "consumable__location", "consumable__model__category"]
    search_fields = ["consumable__model__name", "note", "recipient__last_name"]
    list_select_related = [
        "consumable__model__manufacturer",
        "consumable__location",
        "performed_by",
        "recipient",
    ]
    date_hierarchy = "created_at"

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: ConsumableMovement | None = None) -> bool:
        return False
