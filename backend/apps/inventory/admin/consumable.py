from django.contrib import admin
from django.db.models import F
from django.utils.translation import gettext_lazy as _

from apps.inventory.models import Consumable, ConsumableMovement


class ConsumableMovementInline(admin.TabularInline):
    model = ConsumableMovement
    extra = 0
    fields = ["created_at", "delta", "reason", "note", "performed_by", "recipient"]
    readonly_fields = fields
    can_delete = False
    ordering = ["-created_at"]

    def has_add_permission(self, request, obj=None) -> bool:
        # Movements change the quantity; book them in the app so both stay consistent.
        return False


class BelowMinimumFilter(admin.SimpleListFilter):
    title = _("stock level")
    parameter_name = "level"

    def lookups(self, request, model_admin):
        return [("low", _("Below minimum"))]

    def queryset(self, request, queryset):
        return queryset.filter(quantity__lt=F("min_quantity")) if self.value() == "low" else queryset


@admin.register(Consumable)
class ConsumableAdmin(admin.ModelAdmin):
    list_display = ["model", "location", "quantity", "reserved_quantity", "min_quantity", "is_below_minimum"]
    list_filter = [BelowMinimumFilter, "location", "model__category"]
    search_fields = ["model__name", "model__ean", "location__name"]
    list_select_related = ["model__manufacturer", "location"]
    autocomplete_fields = ["model", "location"]
    readonly_fields = ["quantity", "reserved_quantity", "created_at", "updated_at"]
    inlines = [ConsumableMovementInline]

    @admin.display(boolean=True, description=_("below minimum"))
    def is_below_minimum(self, obj: Consumable) -> bool:
        return obj.is_below_minimum
