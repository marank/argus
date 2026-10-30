"""Site-wide notification switches per kind and channel (administrators only)."""

from typing import TypedDict

from ninja import Router, Schema

from apps.core.api.security import AuthedRequest, superuser_auth
from apps.core.models import MailSettings
from apps.core.notifications import EVENT_KEYS, mail_ready, site_events

router = Router(tags=["settings"], auth=superuser_auth)


class NotificationSettingsOut(Schema):
    # Email needs the mail setup; without it the email switches have no effect.
    mail_ready: bool
    mail: dict[str, bool]
    app: dict[str, bool]


class NotificationSettingsIn(Schema):
    mail: dict[str, bool] = {}
    app: dict[str, bool] = {}


class Switches(TypedDict):
    mail_ready: bool
    mail: dict[str, bool]
    app: dict[str, bool]


def _out(settings: MailSettings) -> Switches:
    return {
        "mail_ready": mail_ready(settings),
        "mail": site_events(settings.events),
        "app": site_events(settings.app_events),
    }


def _known(switches: dict[str, bool]) -> dict[str, bool]:
    return {key: bool(value) for key, value in switches.items() if key in EVENT_KEYS}


@router.get("", response=NotificationSettingsOut)
def get_notification_settings(request: AuthedRequest) -> Switches:
    return _out(MailSettings.load())


@router.put("", response=NotificationSettingsOut)
def update_notification_settings(request: AuthedRequest, payload: NotificationSettingsIn) -> Switches:
    settings = MailSettings.load()
    settings.events = {**settings.events, **_known(payload.mail)}
    settings.app_events = {**settings.app_events, **_known(payload.app)}
    settings.save(update_fields=["events", "app_events", "updated_at"])
    return _out(settings)
