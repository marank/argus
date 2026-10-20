"""Email notifications.

Every notification kind is listed in ``EVENTS`` with its audience. It goes out
when mail is enabled, the kind is on in the mail settings and the recipient has
not switched it off for themselves (``User.notification_settings``). Mails are
sent after the surrounding transaction commits; a failing server is logged and
never breaks the action that caused the mail.
"""

import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from django.conf import settings as django_settings
from django.core.mail import EmailMessage
from django.db import IntegrityError, transaction
from django.utils import translation
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Event:
    key: str
    audience: str  # "employee": the person concerned; "it": the IT department


EVENTS: tuple[Event, ...] = (
    Event("request_submitted", "it"),
    Event("issue_reported", "it"),
    Event("assigned_to_me", "it"),
    Event("license_expiring", "it"),
    Event("request_approved", "employee"),
    Event("request_rejected", "employee"),
    Event("request_ready", "employee"),
    Event("return_reminder", "employee"),
    Event("return_overdue", "employee"),
    Event("issue_resolved", "employee"),
)
EVENT_KEYS = {event.key for event in EVENTS}
AUDIENCE = {event.key: event.audience for event in EVENTS}


def site_events(stored: dict) -> dict[str, bool]:
    """Notification kinds switched on site-wide (all on by default)."""
    return {event.key: bool(stored.get(event.key, True)) for event in EVENTS}


def user_wants(user, event: str) -> bool:
    return bool((user.notification_settings or {}).get(event, True))


def it_staff():
    from apps.accounts.models import User

    return User.objects.filter(is_active=True, is_terminal=False).filter(is_staff=True)


SMTP_BACKEND = "django.core.mail.backends.smtp.EmailBackend"


def connection(settings):
    """SMTP backend built from the mail settings in the database.

    Tests swap in Django's in-memory backend via ARGUS_EMAIL_BACKEND.
    """
    path = getattr(django_settings, "ARGUS_EMAIL_BACKEND", SMTP_BACKEND)
    if path != SMTP_BACKEND:
        return import_string(path)()
    return import_string(path)(
        host=settings.host,
        port=settings.port,
        username=settings.username or None,
        password=settings.password or None,
        use_tls=settings.security == settings.Security.STARTTLS,
        use_ssl=settings.security == settings.Security.SSL,
        timeout=15,
    )


def sender(settings) -> str:
    return f"{settings.from_name} <{settings.from_email}>" if settings.from_name else settings.from_email


def link(settings, path: str) -> str:
    return f"{settings.app_url.rstrip('/')}{path}" if settings.app_url else ""


def send_mail(settings, to: str, subject: str, body: str) -> None:
    with connection(settings) as backend:
        backend.send_messages([EmailMessage(subject, body, sender(settings), [to])])


Render = Callable[[object], tuple[str, str]]


def notify(event: str, recipients: Iterable, render: Render, *, key: str = "", path: str = "") -> None:
    """Queue ``event`` for each recipient; ``render(user)`` returns (subject, body).

    With ``key``, each recipient gets the notification only once (reminders).
    ``path`` is appended as a link when the app address is configured.
    """
    from apps.core.models import MailSettings, NotificationLog

    settings = MailSettings.load()
    if not (settings.enabled and settings.host and settings.from_email):
        return
    if not site_events(settings.events)[event]:
        return

    messages = []
    for user in recipients:
        if not user.email or not user.is_active or not user_wants(user, event):
            continue
        if key:
            try:
                with transaction.atomic():
                    NotificationLog.objects.create(event=event, key=key, recipient=user)
            except IntegrityError:
                continue  # already sent
        with translation.override(user.language or "de"):
            subject, body = render(user)
            url = link(settings, path)
            if url:
                body = f"{body}\n\n{url}"
        messages.append((user.email, subject, body))

    def deliver():
        for to, subject, body in messages:
            try:
                send_mail(settings, to, subject, body)
            except Exception:  # noqa: BLE001 - mail problems must not break the app
                logger.exception("Could not send %s notification to %s", event, to)

    if messages:
        transaction.on_commit(deliver)
