from django.contrib import admin

from apps.accounts.models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "cost_center"]
    search_fields = ["name", "code", "cost_center"]
