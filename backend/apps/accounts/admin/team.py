from django.contrib import admin
from django.db.models import Count
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import Team


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "ldap_group_dn", "member_count"]
    search_fields = ["name", "code", "ldap_group_dn"]
    autocomplete_fields = ["members"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_members=Count("members"))

    @admin.display(description=_("members"), ordering="_members")
    def member_count(self, obj) -> int:
        return obj._members
