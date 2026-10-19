from django.contrib import admin

from apps.core.models import NumberSequence


@admin.register(NumberSequence)
class NumberSequenceAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "pattern", "next_value", "reset_period", "preview"]
    search_fields = ["name", "code", "prefix"]
