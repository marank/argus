from django.contrib import admin

from apps.masterdata.models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "parent", "number_sequence", "is_requestable"]
    search_fields = ["name", "code"]
