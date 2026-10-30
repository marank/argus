from typing import Any

from django import forms
from django.contrib import admin, messages
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import LdapSettings
from apps.accounts.services import ldap


class LdapSettingsForm(forms.ModelForm[LdapSettings]):
    bind_password = forms.CharField(
        label=_("bind password"),
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text=_("Leave empty to keep the stored password."),
    )
    clear_bind_password = forms.BooleanField(label=_("clear bind password"), required=False)

    class Meta:
        model = LdapSettings
        fields = ldap.CONFIG_FIELDS

    def clean(self) -> dict[str, Any]:
        super().clean()
        data = self.cleaned_data
        if data.get("clear_bind_password"):
            data["bind_password"] = ""
        elif not data.get("bind_password"):
            data["bind_password"] = self.instance.bind_password
        return data


@admin.register(LdapSettings)
class LdapSettingsAdmin(admin.ModelAdmin[LdapSettings]):
    """Single settings row; fields set via LDAP_* environment variables are read-only."""

    form = LdapSettingsForm
    fieldsets = [
        (None, {"fields": ["enabled", "create_users"]}),
        (_("Server"), {"fields": ["server_uri", "start_tls", "verify_cert", "ca_cert_file", "timeout"]}),
        (
            _("Search"),
            {
                "fields": [
                    "bind_dn",
                    "bind_password",
                    "clear_bind_password",
                    "user_search_base",
                    "user_filter",
                ]
            },
        ),
        (
            _("Attribute mapping"),
            {
                "fields": [
                    "attr_username",
                    "attr_first_name",
                    "attr_last_name",
                    "attr_employee_number",
                    "attr_email",
                    "attr_job_title",
                    "attr_phone",
                ]
            },
        ),
    ]

    def has_module_permission(self, request: HttpRequest) -> bool:
        return request.user.is_superuser

    def has_view_permission(self, request: HttpRequest, obj: LdapSettings | None = None) -> bool:
        return request.user.is_superuser

    def has_change_permission(self, request: HttpRequest, obj: LdapSettings | None = None) -> bool:
        return request.user.is_superuser

    def has_add_permission(self, request: HttpRequest) -> bool:
        return request.user.is_superuser and not LdapSettings.objects.exists()

    def has_delete_permission(self, request: HttpRequest, obj: LdapSettings | None = None) -> bool:
        return False

    def get_readonly_fields(self, request: HttpRequest, obj: LdapSettings | None = None) -> list[str]:
        locked = set(ldap.env_overrides())
        if "bind_password" in locked:
            locked.add("clear_bind_password")
        return sorted(locked)

    def render_change_form(
        self, request: HttpRequest, context: dict[str, Any], *args: Any, **kwargs: Any
    ) -> HttpResponse:
        locked = ldap.env_overrides()
        if locked and request.method == "GET":
            names = ", ".join(ldap.env_name(field) for field in sorted(locked))
            messages.info(request, _("Set by environment variables (read-only here): %s") % names)
        return super().render_change_form(request, context, *args, **kwargs)
