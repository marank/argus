from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.core.models import NumberSequence


@admin.register(NumberSequence)
class NumberSequenceAdmin(admin.ModelAdmin[NumberSequence]):
    list_display = ["name", "code", "pattern", "next_value", "reset_period", "next_number"]
    list_filter = ["reset_period"]
    search_fields = ["name", "code", "prefix"]
    readonly_fields = ["period_key", "next_number", "created_at", "updated_at"]
    fieldsets = [
        (None, {"fields": ["name", "code"]}),
        (_("Format"), {"fields": ["prefix", "pattern", "padding", "reset_period"]}),
        (_("State"), {"fields": ["next_value", "period_key", "next_number"]}),
        (_("History"), {"fields": ["created_at", "updated_at"], "classes": ["collapse"]}),
    ]

    @admin.display(description=_("next number"))
    def next_number(self, obj: NumberSequence) -> str:
        return obj.preview()
