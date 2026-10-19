"""LDAP login settings (administrators only)."""

from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError

from apps.accounts.models import LdapSettings
from apps.accounts.schemas import LdapSettingsIn, LdapSettingsOut, LdapTestIn, LdapTestOut
from apps.accounts.services import ldap
from apps.core.api.security import superuser_auth

router = Router(tags=["settings"], auth=superuser_auth)


def _out(config: ldap.LdapConfig) -> dict:
    values = {field: getattr(config, field) for field in ldap.CONFIG_FIELDS if field != "bind_password"}
    return {
        **values,
        "bind_password_set": bool(config.bind_password),
        "locked": sorted(config.locked),
        "env_names": {field: ldap.env_name(field) for field in ldap.CONFIG_FIELDS},
    }


def _changes(payload: LdapSettingsIn) -> dict:
    data = payload.dict(include=set(ldap.CONFIG_FIELDS))
    if data.get("bind_password") is None:
        data.pop("bind_password", None)
    return data


@router.get("", response=LdapSettingsOut)
def get_settings(request: HttpRequest):
    return _out(ldap.load_config())


@router.put("", response=LdapSettingsOut)
def update_settings(request: HttpRequest, payload: LdapSettingsIn):
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
def test_settings(request: HttpRequest, payload: LdapTestIn):
    """Try the (possibly unsaved) configuration: service bind and optional user lookup."""
    config = ldap.load_config(**_changes(payload))
    try:
        return ldap.test_connection(config, payload.username.strip())
    except ldap.LdapError as exc:
        raise HttpError(400, str(exc)) from exc
