from django.contrib import admin
from django.db.models import Count, QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import Team


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin[Team]):
    list_display = ["name", "code", "is_default", "ldap_group_dn", "member_count"]
    search_fields = ["name", "code", "ldap_group_dn"]
    autocomplete_fields = ["members"]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Team]:
        return super().get_queryset(request).annotate(_members=Count("members"))

    @admin.display(description=_("members"), ordering="_members")
    def member_count(self, obj: Team) -> int:
        # Annotated by get_queryset.
        count: int = obj._members  # type: ignore[attr-defined]
        return count
