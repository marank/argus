from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from apps.accounts.models import User
from apps.accounts.services import two_factor


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        "username",
        "first_name",
        "last_name",
        "email",
        "department",
        "is_staff",
        "is_terminal",
        "is_active",
        "two_factor_method",
    ]
    list_filter = ["is_staff", "is_terminal", "is_superuser", "is_active", "department", "language"]
    search_fields = ["username", "first_name", "last_name", "email", "employee_number"]
    list_select_related = ["department", "two_factor"]
    actions = ["reset_two_factor"]
    autocomplete_fields = ["department"]
    fieldsets = (
        *BaseUserAdmin.fieldsets,
        (
            _("Organisation"),
            {"fields": ("department", "employee_number", "job_title", "phone", "language")},
        ),
        (_("Argus roles"), {"fields": ("approval_exempt", "is_terminal", "terminal_location")}),
        (_("Directory"), {"fields": ("ldap_dn",)}),
        (_("Two-factor authentication"), {"fields": ("two_factor_method",)}),
    )
    readonly_fields = ["ldap_dn", "two_factor_method"]
    add_fieldsets = (
        *BaseUserAdmin.add_fieldsets,
        (_("Organisation"), {"fields": ("first_name", "last_name", "email", "department")}),
    )

    @admin.display(description=_("two-factor authentication"))
    def two_factor_method(self, obj: User) -> str:
        method = getattr(obj, "two_factor", None)
        return method.get_method_display() if method else "—"

    @admin.action(description=_("Reset two-factor authentication"))
    def reset_two_factor(self, request, queryset):
        users = list(queryset.exclude(pk=request.user.pk))
        if not request.user.is_superuser:
            users = [u for u in users if not u.is_superuser]
        for user in users:
            two_factor.disable(user)
        self.message_user(
            request,
            ngettext(
                "Two-factor authentication reset for %(count)d user.",
                "Two-factor authentication reset for %(count)d users.",
                len(users),
            )
            % {"count": len(users)},
            messages.SUCCESS,
        )
