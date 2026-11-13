"""Site settings: everyone reads them, administrators change them.

Modules and features, deadlines, which email notifications exist (so users
can see what they may switch off for themselves), and whether LDAP login is on.
"""

from typing import Any

from ninja import Field, Router

from apps.core.api.security import AuthedRequest, session_auth, superuser_auth
from apps.core.features import FLAG_KEYS, FLAGS, FlagKey, FlagKind, ModuleKey, current_flags
from apps.core.models import MailSettings, SiteSettings
from apps.core.models.site_settings import RULE_FIELDS
from apps.core.notifications import EVENTS, NotificationAudience, NotificationEvent, mail_ready, site_events
from apps.core.schemas.base import Schema

router = Router(tags=["settings"])


class FlagOut(Schema):
    key: FlagKey
    kind: FlagKind
    requires: list[ModuleKey]


class RulesSchema(Schema):
    warranty_warning_days: int = Field(..., ge=1, le=365)
    license_warning_days: int = Field(..., ge=1, le=365)
    default_loan_days: int = Field(..., ge=1, le=365)
    max_loan_days: int = Field(..., ge=0, le=3650)
    return_reminder_days: int = Field(..., ge=0, le=60)
    # How long a sign-in lasts; a user's own value overrides it.
    session_hours: int = Field(..., ge=1, le=720)


class NotificationEventOut(Schema):
    key: NotificationEvent
    audience: NotificationAudience
    # Switched on site-wide, per channel.
    mail: bool
    app: bool


class SiteSettingsOut(Schema):
    # Effective values: a feature is off while a module it needs is off.
    flags: dict[FlagKey, bool]
    # What the administrator switched, before dependencies are applied.
    stored: dict[FlagKey, bool]
    definitions: list[FlagOut]
    rules: RulesSchema
    mail_enabled: bool
    # Directory login is configured and on: forms show the LDAP-related fields.
    ldap_enabled: bool
    notifications: list[NotificationEventOut]


class SiteSettingsIn(Schema):
    flags: dict[str, bool] = {}
    rules: RulesSchema | None = None


def _ldap_enabled() -> bool:
    from apps.accounts.services.ldap import LdapError, load_config

    try:
        return load_config().is_usable
    except LdapError:
        return False


def _out() -> dict[str, Any]:
    site = SiteSettings.load()
    mail = MailSettings.load()
    mail_events, app_events = site_events(mail.events), site_events(mail.app_events)
    return {
        "flags": current_flags(),
        "stored": {flag.key: bool(site.flags.get(flag.key, True)) for flag in FLAGS},
        "definitions": [
            {"key": flag.key, "kind": flag.kind, "requires": list(flag.requires)} for flag in FLAGS
        ],
        "rules": {name: getattr(site, name) for name in RULE_FIELDS},
        # Email can actually go out: on, with a server and a sender.
        "mail_enabled": mail_ready(mail),
        "ldap_enabled": _ldap_enabled(),
        "notifications": [
            {
                "key": event.key,
                "audience": event.audience,
                "mail": mail_events[event.key],
                "app": app_events[event.key],
            }
            for event in EVENTS
        ],
    }


@router.get("", response=SiteSettingsOut, auth=session_auth)
def get_site_settings(request: AuthedRequest) -> dict[str, Any]:
    return _out()


@router.put("", response=SiteSettingsOut, auth=superuser_auth)
def update_site_settings(request: AuthedRequest, payload: SiteSettingsIn) -> dict[str, Any]:
    site = SiteSettings.load()
    site.flags = {**site.flags, **{k: v for k, v in payload.flags.items() if k in FLAG_KEYS}}
    if payload.rules:
        for name, value in payload.rules.dict().items():
            setattr(site, name, value)
    site.save()
    return _out()
