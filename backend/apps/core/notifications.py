"""Email notifications.

Every notification kind is listed in ``EVENTS`` with its audience. It goes out
when mail is enabled, the kind is on in the mail settings and the recipient has
not switched it off for themselves (``User.notification_settings``). Mails are
queued as background jobs together with the surrounding transaction
(``apps.core.jobs``); a failing server never breaks the action that caused the mail.
"""

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from django.conf import settings as django_settings
from django.core.mail import EmailMessage
from django.utils import translation
from django.utils.module_loading import import_string


@dataclass(frozen=True)
class Event:
    key: str
    # "employee": the person concerned; "it": the IT department; "approver": department approvers
    audience: str


EVENTS: tuple[Event, ...] = (
    Event("approval_requested", "approver"),
    Event("request_submitted", "it"),
    Event("issue_reported", "it"),
    Event("issue_answered", "it"),
    Event("assigned_to_me", "it"),
    Event("license_expiring", "it"),
    Event("request_confirmed", "employee"),
    Event("request_rejected", "employee"),
    Event("request_ready", "employee"),
    Event("return_reminder", "employee"),
    Event("return_overdue", "employee"),
    Event("issue_message", "employee"),
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


def mail_ready(settings) -> bool:
    return bool(settings.enabled and settings.host and settings.from_email)


def notify(
    event: str,
    recipients: Iterable,
    render: Render,
    *,
    key: str = "",
    path: str = "",
    direct: bool = False,
) -> None:
    """Queue ``event`` for each recipient; ``render(user)`` returns (subject, body).

    With ``key``, each recipient gets the notification only once (reminders): it
    counts as sent once delivered, and is not queued again while it waits for a
    retry. ``path`` is appended as a link when the app address is configured.
    ``direct``: sent on purpose by IT (not listed in ``EVENTS``), so the site-wide
    and personal switches do not apply.
    """
    from apps.core import tasks
    from apps.core.jobs import defer
    from apps.core.models import MailSettings, NotificationLog

    settings = MailSettings.load()
    if not mail_ready(settings):
        return
    if not direct and not site_events(settings.events)[event]:
        return

    for user in recipients:
        if not user.email or not user.is_active or not (direct or user_wants(user, event)):
            continue
        if key and NotificationLog.objects.filter(event=event, key=key, recipient=user).exists():
            continue  # already sent
        with translation.override(user.language or "de"):
            subject, body = render(user)
            url = link(settings, path)
            if url:
                body = f"{body}\n\n{url}"
        defer(
            tasks.send_notification,
            queueing_lock=f"{event}:{key}:{user.pk}" if key else None,
            event=event,
            to=user.email,
            subject=subject,
            body=body,
            key=key,
            recipient=str(user.pk),
        )
