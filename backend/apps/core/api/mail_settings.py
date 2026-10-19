"""SMTP server and site-wide notification switches (administrators only)."""

from django.http import HttpRequest
from django.utils.translation import gettext as _
from ninja import Router, Schema
from ninja.errors import HttpError

from apps.core.api.security import superuser_auth
from apps.core.models import MailSettings
from apps.core.notifications import EVENT_KEYS, send_mail, site_events

router = Router(tags=["settings"], auth=superuser_auth)


class MailSettingsOut(Schema):
    enabled: bool
    host: str
    port: int
    security: str
    username: str
    password_set: bool
    from_email: str
    from_name: str
    app_url: str
    events: dict[str, bool]


class MailSettingsIn(Schema):
    enabled: bool = False
    host: str = ""
    port: int = 587
    security: MailSettings.Security = MailSettings.Security.STARTTLS
    username: str = ""
    # None keeps the stored password; "" removes it.
    password: str | None = None
    from_email: str = ""
    from_name: str = "Argus"
    app_url: str = ""
    events: dict[str, bool] = {}


class TestMailIn(Schema):
    to: str


def _out(settings: MailSettings) -> dict:
    return {
        "enabled": settings.enabled,
        "host": settings.host,
        "port": settings.port,
        "security": settings.security,
        "username": settings.username,
        "password_set": bool(settings.password),
        "from_email": settings.from_email,
        "from_name": settings.from_name,
        "app_url": settings.app_url,
        "events": site_events(settings.events),
    }


@router.get("", response=MailSettingsOut)
def get_mail_settings(request: HttpRequest):
    return _out(MailSettings.load())


@router.put("", response=MailSettingsOut)
def update_mail_settings(request: HttpRequest, payload: MailSettingsIn):
    settings = MailSettings.load()
    data = payload.dict()
    password = data.pop("password")
    events = data.pop("events")
    for name, value in data.items():
        setattr(settings, name, value)
    if password is not None:
        settings.password = password
    settings.events = {**settings.events, **{k: v for k, v in events.items() if k in EVENT_KEYS}}
    if settings.enabled and not (settings.host and settings.from_email):
        raise HttpError(422, _("Enter the SMTP server and the sender address to send emails."))
    settings.full_clean()
    settings.save()
    return _out(settings)


@router.post("/test", response={200: dict})
def send_test_mail(request: HttpRequest, payload: TestMailIn):
    """Send a test email with the stored settings."""
    settings = MailSettings.load()
    if not (settings.host and settings.from_email):
        raise HttpError(422, _("Enter the SMTP server and the sender address first."))
    try:
        send_mail(
            settings,
            payload.to,
            _("Argus test email"),
            _("If you can read this, Argus can send emails."),
        )
    except Exception as exc:  # noqa: BLE001 - report every SMTP problem to the admin
        raise HttpError(502, _("Sending failed: %(error)s") % {"error": exc}) from exc
    return {"detail": _("Test email sent to %(to)s.") % {"to": payload.to}}
