from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User


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
    ]
    list_filter = ["is_staff", "is_terminal", "is_superuser", "is_active", "department", "language"]
    search_fields = ["username", "first_name", "last_name", "email", "employee_number"]
    list_select_related = ["department"]
    autocomplete_fields = ["department"]
    fieldsets = (
        *BaseUserAdmin.fieldsets,
        (
            _("Organisation"),
            {"fields": ("department", "employee_number", "job_title", "phone", "language")},
        ),
        (_("Argus roles"), {"fields": ("is_terminal",)}),
    )
    add_fieldsets = (
        *BaseUserAdmin.add_fieldsets,
        (_("Organisation"), {"fields": ("first_name", "last_name", "email", "department")}),
    )
