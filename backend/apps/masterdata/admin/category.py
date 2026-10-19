from django.contrib import admin

from apps.masterdata.models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "code",
        "parent",
        "number_sequence",
        "is_requestable",
        "allow_any_model",
        "sort_order",
    ]
    list_filter = ["is_requestable", "allow_any_model", "parent"]
    list_editable = ["sort_order"]
    search_fields = ["name", "code"]
    list_select_related = ["parent", "number_sequence"]
    autocomplete_fields = ["parent", "number_sequence"]
