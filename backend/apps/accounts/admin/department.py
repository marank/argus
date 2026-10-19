from django.contrib import admin
from django.db.models import Count
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "cost_center", "member_count"]
    search_fields = ["name", "code", "cost_center"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_members=Count("members"))

    @admin.display(description=_("members"), ordering="_members")
    def member_count(self, obj) -> int:
        return obj._members
