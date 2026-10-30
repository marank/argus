from django.contrib import admin
from django.db.models import Count, QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin[Department]):
    list_display = ["name", "parent", "icon", "code", "cost_center", "member_count"]
    search_fields = ["name", "code", "cost_center"]
    autocomplete_fields = ["parent", "approvers"]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Department]:
        return super().get_queryset(request).annotate(_members=Count("members"))

    @admin.display(description=_("members"), ordering="_members")
    def member_count(self, obj: Department) -> int:
        # Annotated by get_queryset.
        count: int = obj._members  # type: ignore[attr-defined]
        return count
