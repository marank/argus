from django.contrib import admin

from apps.masterdata.models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin[Category]):
    list_display = [
        "name",
        "code",
        "parent",
        "number_sequence",
        "team",
        "is_requestable",
        "model_choice",
        "requires_approval",
        "is_accessory",
        "sort_order",
    ]
    list_filter = ["is_requestable", "model_choice", "requires_approval", "is_accessory", "parent"]
    list_editable = ["sort_order"]
    search_fields = ["name", "code", "identifier_label"]
    list_select_related = ["parent", "number_sequence", "team"]
    autocomplete_fields = ["parent", "number_sequence", "team"]
