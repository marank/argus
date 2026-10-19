"""Site settings: everyone reads them, administrators change them.

Modules and features, deadlines, and which email notifications exist (so users
can see what they may switch off for themselves).
"""

from django.http import HttpRequest
from ninja import Field, Router, Schema

from apps.core.api.security import session_auth, superuser_auth
from apps.core.features import FLAG_KEYS, FLAGS, current_flags
from apps.core.models import MailSettings, SiteSettings
from apps.core.models.site_settings import RULE_FIELDS
from apps.core.notifications import EVENTS, site_events

router = Router(tags=["settings"])


class FlagOut(Schema):
    key: str
    kind: str
    requires: list[str]


class RulesSchema(Schema):
    warranty_warning_days: int = Field(..., ge=1, le=365)
    license_warning_days: int = Field(..., ge=1, le=365)
    default_loan_days: int = Field(..., ge=1, le=365)
    max_loan_days: int = Field(..., ge=0, le=3650)
    return_reminder_days: int = Field(..., ge=0, le=60)


class NotificationEventOut(Schema):
    key: str
    audience: str
    enabled: bool


class SiteSettingsOut(Schema):
    # Effective values: a feature is off while a module it needs is off.
    flags: dict[str, bool]
    # What the administrator switched, before dependencies are applied.
    stored: dict[str, bool]
    definitions: list[FlagOut]
    rules: RulesSchema
    mail_enabled: bool
    notifications: list[NotificationEventOut]


class SiteSettingsIn(Schema):
    flags: dict[str, bool] = {}
    rules: RulesSchema | None = None


def _out() -> dict:
    site = SiteSettings.load()
    mail = MailSettings.load()
    events = site_events(mail.events)
    return {
        "flags": current_flags(),
        "stored": {flag.key: bool(site.flags.get(flag.key, True)) for flag in FLAGS},
        "definitions": [
            {"key": flag.key, "kind": flag.kind, "requires": list(flag.requires)} for flag in FLAGS
        ],
        "rules": {name: getattr(site, name) for name in RULE_FIELDS},
        "mail_enabled": mail.enabled,
        "notifications": [
            {"key": event.key, "audience": event.audience, "enabled": events[event.key]} for event in EVENTS
        ],
    }


@router.get("", response=SiteSettingsOut, auth=session_auth)
def get_site_settings(request: HttpRequest):
    return _out()


@router.put("", response=SiteSettingsOut, auth=superuser_auth)
def update_site_settings(request: HttpRequest, payload: SiteSettingsIn):
    site = SiteSettings.load()
    site.flags = {**site.flags, **{k: v for k, v in payload.flags.items() if k in FLAG_KEYS}}
    if payload.rules:
        for name, value in payload.rules.dict().items():
            setattr(site, name, value)
    site.save()
    return _out()
