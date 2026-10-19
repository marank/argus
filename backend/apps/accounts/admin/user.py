from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "first_name", "last_name", "department", "is_staff", "is_active"]
    list_filter = ["is_staff", "is_terminal", "is_active", "department"]
    fieldsets = (
        *BaseUserAdmin.fieldsets,
        (
            _("Organisation"),
            {"fields": ("department", "employee_number", "job_title", "phone", "language", "is_terminal")},
        ),
    )
