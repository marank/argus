from django.contrib import admin
from django.http import HttpRequest

from apps.accounts.models import Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin[Role]):
    list_display = ["name", "description"]
    search_fields = ["name", "description"]
    autocomplete_fields = ["members"]

    # Who may change what is decided by administrators only.
    def has_module_permission(self, request: HttpRequest) -> bool:
        return request.user.is_superuser

    def has_view_permission(self, request: HttpRequest, obj: Role | None = None) -> bool:
        return request.user.is_superuser

    def has_add_permission(self, request: HttpRequest) -> bool:
        return request.user.is_superuser

    def has_change_permission(self, request: HttpRequest, obj: Role | None = None) -> bool:
        return request.user.is_superuser

    def has_delete_permission(self, request: HttpRequest, obj: Role | None = None) -> bool:
        return request.user.is_superuser
