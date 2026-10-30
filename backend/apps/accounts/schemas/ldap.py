from typing import Literal

from ninja import Field

from apps.core.schemas.base import Schema


class LdapSettingsBase(Schema):
    enabled: bool
    server_uri: str
    start_tls: bool
    verify_cert: bool
    ca_cert_file: str
    timeout: int = Field(ge=1, le=120)
    bind_dn: str
    user_search_base: str
    user_filter: str
    attr_username: str
    attr_first_name: str
    attr_last_name: str
    attr_employee_number: str
    attr_email: str
    attr_job_title: str
    attr_phone: str
    create_users: bool


class LdapSettingsOut(LdapSettingsBase):
    """Effective configuration; the bind password itself is never returned."""

    bind_password_set: bool
    locked: list[str] = Field(description="Fields set by LDAP_* environment variables (read-only).")
    env_names: dict[str, str]


class LdapSettingsIn(LdapSettingsBase):
    # None keeps the stored password, "" clears it.
    bind_password: str | None = None


class LdapTestIn(LdapSettingsIn):
    username: str = ""


class LdapTestOut(Schema):
    server: str
    user: dict[str, str] | None


class LdapSyncQueryIn(Schema):
    filter: str = Field(max_length=2000)
    search_base: str = Field("", max_length=500, description="Empty = the configured user search base.")


class LdapSyncApplyIn(LdapSyncQueryIn):
    dns: list[str] = Field(description="Entries to take over, from the preview.")


class LdapSyncChange(Schema):
    old: str
    new: str


class LdapSyncItemOut(Schema):
    dn: str
    username: str
    action: Literal["create", "update", "unchanged", "skipped"]
    reason: str = Field(description="Why skipped: no_username, duplicate or superuser")
    user_id: str | None
    values: dict[str, str]
    changes: dict[str, LdapSyncChange]


class LdapSyncPreviewOut(Schema):
    items: list[LdapSyncItemOut]
    truncated: bool
    limit: int


class LdapSyncResultOut(Schema):
    created: int
    updated: int
    skipped: int
