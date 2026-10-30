"""LDAP login settings and user sync (administrators only)."""

from typing import Any, TypedDict

from django.utils.translation import gettext as _
from ninja import Router
from ninja.errors import HttpError

from apps.accounts.models import LdapSettings
from apps.accounts.schemas import (
    LdapSettingsIn,
    LdapSettingsOut,
    LdapSyncApplyIn,
    LdapSyncPreviewOut,
    LdapSyncQueryIn,
    LdapSyncResultOut,
    LdapTestIn,
    LdapTestOut,
)
from apps.accounts.services import ldap
from apps.core.api.security import AuthedRequest, superuser_auth

router = Router(tags=["settings"], auth=superuser_auth)


def _out(config: ldap.LdapConfig) -> dict[str, Any]:
    values = {field: getattr(config, field) for field in ldap.CONFIG_FIELDS if field != "bind_password"}
    return {
        **values,
        "bind_password_set": bool(config.bind_password),
        "locked": sorted(config.locked),
        "env_names": {field: ldap.env_name(field) for field in ldap.CONFIG_FIELDS},
    }


# Where the service account's password goes; changing one of them needs the password again.
TARGET_FIELDS = ("server_uri", "bind_dn", "start_tls", "verify_cert", "ca_cert_file")


def _changes(payload: LdapSettingsIn) -> dict[str, Any]:
    data = payload.dict(include=set(ldap.CONFIG_FIELDS))
    if data.get("bind_password") is None:
        data.pop("bind_password", None)
        # The stored password (possibly from LDAP_BIND_PASSWORD, which admins never see)
        # must not be sent to a server it was not set for.
        current = ldap.load_config()
        changed = [f for f in TARGET_FIELDS if f in data and data[f] != getattr(current, f)]
        if current.bind_password and any(f not in current.locked for f in changed):
            raise HttpError(400, _("Enter the bind password again when changing the server or bind DN."))
    return data


@router.get("", response=LdapSettingsOut)
def get_settings(request: AuthedRequest) -> dict[str, Any]:
    return _out(ldap.load_config())


@router.put("", response=LdapSettingsOut)
def update_settings(request: AuthedRequest, payload: LdapSettingsIn) -> dict[str, Any]:
    stored = LdapSettings.load()
    locked = ldap.env_overrides().keys()
    # Fields set by the environment are left untouched in the database.
    for field, value in _changes(payload).items():
        if field not in locked:
            setattr(stored, field, value)
    stored.full_clean()
    stored.save()
    return _out(ldap.load_config(stored))


@router.post("/test", response=LdapTestOut)
def test_settings(request: AuthedRequest, payload: LdapTestIn) -> ldap.ConnectionTest:
    """Try the (possibly unsaved) configuration: service bind and optional user lookup."""
    config = ldap.load_config(**_changes(payload))
    try:
        return ldap.test_connection(config, payload.username.strip())
    except ldap.LdapError as exc:
        raise HttpError(400, str(exc)) from exc


def _sync_config() -> ldap.LdapConfig:
    """The saved configuration; the sync never runs on unsaved form values."""
    config = ldap.load_config()
    if not config.is_usable:
        raise HttpError(400, _("LDAP login is not enabled or not fully configured."))
    return config


class ChangeOut(TypedDict):
    old: str
    new: str


class SyncItemOut(TypedDict):
    dn: str
    username: str
    action: str
    reason: str
    user_id: str | None
    values: dict[str, str]
    changes: dict[str, ChangeOut]


class SyncPreviewOut(TypedDict):
    items: list[SyncItemOut]
    truncated: bool
    limit: int


def _item_out(item: ldap.SyncItem) -> SyncItemOut:
    return {
        "dn": item.entry.dn,
        "username": item.entry.username,
        "action": item.action,
        "reason": item.reason,
        "user_id": str(item.user.pk) if item.user else None,
        "values": item.entry.values,
        "changes": {f: {"old": old, "new": new} for f, (old, new) in item.changes.items()},
    }


@router.post("/sync/preview", response=LdapSyncPreviewOut)
def sync_preview(request: AuthedRequest, payload: LdapSyncQueryIn) -> SyncPreviewOut:
    """Which users a filter would create or update; nothing is changed."""
    try:
        result = ldap.preview_sync(_sync_config(), payload.filter, payload.search_base)
    except ldap.LdapError as exc:
        raise HttpError(400, str(exc)) from exc
    return {
        "items": [_item_out(i) for i in result["items"]],
        "truncated": result["truncated"],
        "limit": ldap.SYNC_LIMIT,
    }


@router.post("/sync/apply", response=LdapSyncResultOut)
def sync_apply(request: AuthedRequest, payload: LdapSyncApplyIn) -> dict[str, int]:
    """Create or update the users of the chosen preview entries."""
    try:
        return ldap.apply_sync(_sync_config(), payload.filter, payload.search_base, payload.dns)
    except ldap.LdapError as exc:
        raise HttpError(400, str(exc)) from exc
