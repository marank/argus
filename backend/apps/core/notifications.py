"""Notifications by email and in the app (the bell).

Every notification kind that can be switched off is a ``NotificationEvent``, listed in
``EVENTS`` with its audience. Each channel has its own switches: site-wide in the
notification settings (``MailSettings.events`` for email, ``app_events`` for the app)
and per person (``User.notification_settings`` and ``app_notification_settings``); a
person can only switch off what is on site-wide. Email also needs a working mail
setup; the app does not. Mails are queued as background jobs together with the
surrounding transaction (``apps.core.jobs``); a failing server never breaks the action
that caused the mail. In-app notifications are stored right away and announced to the
recipient's open tabs (``apps.core.live``).
"""

import email.policy
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from email.message import EmailMessage
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

from django.conf import settings as django_settings
from django.core.mail import EmailMultiAlternatives
from django.core.mail.backends.base import BaseEmailBackend
from django.db.models import QuerySet
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.module_loading import import_string

if TYPE_CHECKING:
    from apps.accounts.models import User
    from apps.core.models import MailSettings


class NotificationEvent(StrEnum):
    """Notification kinds that the site and each person can switch off."""

    APPROVAL_REQUESTED = "approval_requested"
    REQUEST_SUBMITTED = "request_submitted"
    ISSUE_REPORTED = "issue_reported"
    ISSUE_ANSWERED = "issue_answered"
    ASSIGNED_TO_ME = "assigned_to_me"
    LICENSE_EXPIRING = "license_expiring"
    REQUEST_CONFIRMED = "request_confirmed"
    REQUEST_REJECTED = "request_rejected"
    REQUEST_CANCELLED = "request_cancelled"
    REQUEST_READY = "request_ready"
    REQUEST_RESCHEDULED = "request_rescheduled"
    REQUEST_HANDED_OUT = "request_handed_out"
    REQUEST_EXTENDED = "request_extended"
    REQUEST_RETURNED = "request_returned"
    RETURN_REMINDER = "return_reminder"
    RETURN_OVERDUE = "return_overdue"
    ISSUE_MESSAGE = "issue_message"
    ISSUE_RESOLVED = "issue_resolved"


class DirectNotification(StrEnum):
    """Sent on purpose by IT; no switch applies (see ``notify``)."""

    RETURN_REQUESTED = "return_requested"


class NotificationAudience(StrEnum):
    EMPLOYEE = "employee"  # the person concerned
    IT = "it"  # the IT department
    APPROVER = "approver"  # department approvers


@dataclass(frozen=True)
class Event:
    key: NotificationEvent
    audience: NotificationAudience


EVENTS: tuple[Event, ...] = (
    Event(NotificationEvent.APPROVAL_REQUESTED, NotificationAudience.APPROVER),
    Event(NotificationEvent.REQUEST_SUBMITTED, NotificationAudience.IT),
    Event(NotificationEvent.ISSUE_REPORTED, NotificationAudience.IT),
    Event(NotificationEvent.ISSUE_ANSWERED, NotificationAudience.IT),
    Event(NotificationEvent.ASSIGNED_TO_ME, NotificationAudience.IT),
    Event(NotificationEvent.LICENSE_EXPIRING, NotificationAudience.IT),
    Event(NotificationEvent.REQUEST_CONFIRMED, NotificationAudience.EMPLOYEE),
    Event(NotificationEvent.REQUEST_REJECTED, NotificationAudience.EMPLOYEE),
    Event(NotificationEvent.REQUEST_CANCELLED, NotificationAudience.EMPLOYEE),
    Event(NotificationEvent.REQUEST_READY, NotificationAudience.EMPLOYEE),
    Event(NotificationEvent.REQUEST_RESCHEDULED, NotificationAudience.EMPLOYEE),
    Event(NotificationEvent.REQUEST_HANDED_OUT, NotificationAudience.EMPLOYEE),
    Event(NotificationEvent.REQUEST_EXTENDED, NotificationAudience.EMPLOYEE),
    Event(NotificationEvent.REQUEST_RETURNED, NotificationAudience.EMPLOYEE),
    Event(NotificationEvent.RETURN_REMINDER, NotificationAudience.EMPLOYEE),
    Event(NotificationEvent.RETURN_OVERDUE, NotificationAudience.EMPLOYEE),
    Event(NotificationEvent.ISSUE_MESSAGE, NotificationAudience.EMPLOYEE),
    Event(NotificationEvent.ISSUE_RESOLVED, NotificationAudience.EMPLOYEE),
)


def known_events(switches: object) -> dict[NotificationEvent, bool]:
    """Stored switches of notification kinds that exist (others are left out)."""
    if not isinstance(switches, dict):
        return {}
    return {
        NotificationEvent(key): bool(value) for key, value in switches.items() if key in NotificationEvent
    }


def site_events(stored: dict[str, object]) -> dict[NotificationEvent, bool]:
    """Notification kinds switched on site-wide (all on by default)."""
    return {event.key: bool(stored.get(event.key, True)) for event in EVENTS}


def receivable(user: User) -> set[NotificationEvent]:
    """Kinds ``user`` can get, and so switch off: their own, plus IT and approver ones by role."""
    audiences = {NotificationAudience.EMPLOYEE}
    if user.is_it_staff:
        audiences.add(NotificationAudience.IT)
    if user.is_approver:
        audiences.add(NotificationAudience.APPROVER)
    return {event.key for event in EVENTS if event.audience in audiences}


def user_wants(user: User, event: NotificationEvent) -> bool:
    return bool((user.notification_settings or {}).get(event, True))


def user_wants_app(user: User, event: NotificationEvent) -> bool:
    return bool((user.app_notification_settings or {}).get(event, True))


def it_staff() -> QuerySet[User]:
    from apps.accounts.models import User

    return User.objects.filter(is_active=True, is_terminal=False).filter(is_staff=True)


SMTP_BACKEND = "django.core.mail.backends.smtp.EmailBackend"


def connection(settings: MailSettings) -> BaseEmailBackend:
    """SMTP backend built from the mail settings in the database.

    Tests swap in Django's in-memory backend via ARGUS_EMAIL_BACKEND.
    """
    path = getattr(django_settings, "ARGUS_EMAIL_BACKEND", SMTP_BACKEND)
    backend: type[BaseEmailBackend] = import_string(path)
    if path != SMTP_BACKEND:
        return backend()
    return backend(
        host=settings.host,
        port=settings.port,
        username=settings.username or None,
        password=settings.password or None,
        use_tls=settings.security == settings.Security.STARTTLS,
        use_ssl=settings.security == settings.Security.SSL,
        timeout=15,
    )


def sender(settings: MailSettings) -> str:
    return f"{settings.from_name} <{settings.from_email}>" if settings.from_name else settings.from_email


def link(settings: MailSettings, path: str) -> str:
    return f"{settings.app_url.rstrip('/')}{path}" if settings.app_url else ""


LOGO_CID = "argus-logo"
LOGO = Path(__file__).parent / "templates" / "core" / "mail" / "logo.png"


class Mail(EmailMultiAlternatives):
    """Plain text plus the HTML part, which carries the logo as an inline image."""

    def message(self, *, policy: email.policy.Policy | None = email.policy.default) -> EmailMessage:
        msg = super().message(policy=policy)
        html = msg.get_body(("html",))
        if html is not None:
            html.add_related(LOGO.read_bytes(), "image", "png", cid=f"<{LOGO_CID}>", filename="argus.png")
        return msg


class Block(TypedDict, total=False):
    """A part of the mail body: a paragraph, a (labelled) list or a code."""

    text: str
    label: str
    lines: list[str]
    code: str


def blocks(body: str, code: str = "") -> list[Block]:
    """The text body as paragraphs and lists ("- " lines, optionally after a "Label:" line).

    ``code`` follows the paragraph that names it, or ends the body.
    """
    result: list[Block] = []
    for part in body.strip().split("\n\n"):
        lines = part.splitlines()
        label = lines[0] if len(lines) > 1 and not lines[0].startswith("- ") else ""
        items = lines[1:] if label else lines
        if items and all(line.startswith("- ") for line in items):
            result.append({"label": label.rstrip(":"), "lines": [line[2:] for line in items]})
        else:
            result.append({"text": part})
            if code and code in part:
                result.append({"code": code})
                code = ""
    if code:
        result.append({"code": code})
    return result


def send_mail(
    settings: MailSettings,
    to: str,
    subject: str,
    body: str,
    *,
    url: str = "",
    code: str = "",
    manage_url: str = "",
) -> None:
    """Sends ``body`` as text and in the HTML layout, in the active language.

    ``url`` is the page the mail is about (a button), ``code`` a code to type in (set
    off large), ``manage_url`` the page where the recipient switches notifications off.
    """
    text = f"{body}\n\n{url}" if url else body
    html = render_to_string(
        "core/mail/message.html",
        {
            "subject": subject,
            "preheader": body.split("\n\n", 1)[0],
            "blocks": blocks(body, code),
            "url": url,
            "manage_url": manage_url,
            "logo_cid": LOGO_CID,
        },
    )
    message = Mail(subject, text, sender(settings), [to])
    message.attach_alternative(html, "text/html")
    with connection(settings) as backend:
        backend.send_messages([message])


Render = Callable[["User"], tuple[str, str]]


def mail_ready(settings: MailSettings) -> bool:
    return bool(settings.enabled and settings.host and settings.from_email)


_muted: ContextVar[bool] = ContextVar("notifications_muted", default=False)


@contextmanager
def muted() -> Iterator[None]:
    """Sends nothing inside: the caller tells whoever needs to know about the whole step."""
    token = _muted.set(True)
    try:
        yield
    finally:
        _muted.reset(token)


def _site_channels(
    event: NotificationEvent | DirectNotification, settings: MailSettings
) -> tuple[bool, bool]:
    """Whether ``event`` goes out by email and in the app at all (site-wide switches)."""
    if isinstance(event, DirectNotification):
        return mail_ready(settings), True
    by_mail = mail_ready(settings) and site_events(settings.events)[event]
    in_app = site_events(settings.app_events)[event]
    return by_mail, in_app


def _user_channels(
    event: NotificationEvent | DirectNotification,
    user: User,
    channels: tuple[bool, bool],
    key: str,
) -> tuple[bool, bool]:
    """The channels of ``channels`` (email, app) by which ``user`` gets ``event``."""
    from apps.core.models import Notification, NotificationLog

    by_mail, in_app = channels
    mail = by_mail and bool(user.email) and (isinstance(event, DirectNotification) or user_wants(user, event))
    app = in_app and (isinstance(event, DirectNotification) or user_wants_app(user, event))
    if key:
        mail = mail and not NotificationLog.objects.filter(event=event, key=key, recipient=user).exists()
        app = app and not Notification.objects.filter(event=event, key=key, recipient=user).exists()
    return mail, app


def _create_in_app(
    event: NotificationEvent | DirectNotification, user: User, subject: str, body: str, key: str, path: str
) -> None:
    from apps.core.live import publish
    from apps.core.models import Notification

    notification = Notification.objects.create(
        recipient=user,
        event=event,
        key=key,
        title=subject[:255],
        # The first paragraph says what happened; the rest (items, link) is for the email.
        text=body.split("\n\n", 1)[0],
        path=path,
    )
    publish("notification", notification.pk, users=[user.pk], staff=False)


def _queue_mail(
    event: NotificationEvent | DirectNotification,
    user: User,
    subject: str,
    body: str,
    *,
    settings: MailSettings,
    key: str,
    path: str,
) -> None:
    from apps.core import tasks
    from apps.core.jobs import defer

    defer(
        tasks.send_notification,
        queueing_lock=f"{event}:{key}:{user.pk}" if key else None,
        event=event,
        to=user.email,
        subject=subject,
        body=body,
        url=link(settings, path),
        language=user.language or "de",
        key=key,
        recipient=str(user.pk),
    )


def notify(
    event: NotificationEvent | DirectNotification,
    recipients: Iterable[User],
    render: Render,
    *,
    key: str = "",
    path: str = "",
) -> None:
    """Notify each recipient of ``event``; ``render(user)`` returns (subject, body).

    By email and in the app, as the switches allow. With ``key``, each recipient gets
    the notification only once per channel (reminders): an email counts as sent once
    delivered, and is not queued again while it waits for a retry. ``path`` is the
    page it is about: the email links to it when the app address is configured, the
    app opens it. A ``DirectNotification`` is sent on purpose by IT, so the site-wide
    and personal switches do not apply.
    """
    from apps.core.models import MailSettings

    if _muted.get():
        return
    settings = MailSettings.load()
    channels = _site_channels(event, settings)
    if not any(channels):
        return

    for user in recipients:
        if not user.is_active or user.is_terminal:
            continue
        mail, app = _user_channels(event, user, channels, key)
        if not (mail or app):
            continue
        with translation.override(user.language or "de"):
            subject, body = render(user)
        if app:
            _create_in_app(event, user, subject, body, key, path)
        if mail:
            _queue_mail(event, user, subject, body, settings=settings, key=key, path=path)
