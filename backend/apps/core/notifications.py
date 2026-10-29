"""Notifications by email and in the app (the bell).

Every notification kind is listed in ``EVENTS`` with its audience. Each channel has
its own switches: site-wide in the notification settings (``MailSettings.events``
for email, ``app_events`` for the app) and per person (``User.notification_settings``
and ``app_notification_settings``); a person can only switch off what is on
site-wide. Email also needs a working mail setup; the app does not. Mails are queued
as background jobs together with the surrounding transaction (``apps.core.jobs``); a
failing server never breaks the action that caused the mail. In-app notifications are
stored right away and announced to the recipient's open tabs (``apps.core.live``).
"""

import email.policy
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings as django_settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
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
    Event("request_cancelled", "employee"),
    Event("request_ready", "employee"),
    Event("request_rescheduled", "employee"),
    Event("request_handed_out", "employee"),
    Event("request_extended", "employee"),
    Event("request_returned", "employee"),
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


def receivable(user) -> set[str]:
    """Kinds ``user`` can get, and so switch off: their own, plus IT and approver ones by role."""
    audiences = {"employee"}
    if user.is_it_staff:
        audiences.add("it")
    if user.is_approver:
        audiences.add("approver")
    return {event.key for event in EVENTS if event.audience in audiences}


def user_wants(user, event: str) -> bool:
    return bool((user.notification_settings or {}).get(event, True))


def user_wants_app(user, event: str) -> bool:
    return bool((user.app_notification_settings or {}).get(event, True))


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


LOGO_CID = "argus-logo"
LOGO = Path(__file__).parent / "templates" / "core" / "mail" / "logo.png"


class Mail(EmailMultiAlternatives):
    """Plain text plus the HTML part, which carries the logo as an inline image."""

    def message(self, *, policy=email.policy.default):
        msg = super().message(policy=policy)
        html = msg.get_body(("html",))
        if html is not None:
            html.add_related(LOGO.read_bytes(), "image", "png", cid=f"<{LOGO_CID}>", filename="argus.png")
        return msg


def blocks(body: str, code: str = "") -> list[dict]:
    """The text body as paragraphs and lists ("- " lines, optionally after a "Label:" line).

    ``code`` follows the paragraph that names it, or ends the body.
    """
    result = []
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
    settings, to: str, subject: str, body: str, *, url: str = "", code: str = "", manage_url: str = ""
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
    """Notify each recipient of ``event``; ``render(user)`` returns (subject, body).

    By email and in the app, as the switches allow. With ``key``, each recipient gets
    the notification only once per channel (reminders): an email counts as sent once
    delivered, and is not queued again while it waits for a retry. ``path`` is the
    page it is about: the email links to it when the app address is configured, the
    app opens it. ``direct``: sent on purpose by IT (not listed in ``EVENTS``), so the
    site-wide and personal switches do not apply.
    """
    from apps.core import tasks
    from apps.core.jobs import defer
    from apps.core.live import publish
    from apps.core.models import MailSettings, Notification, NotificationLog

    settings = MailSettings.load()
    by_mail = mail_ready(settings) and (direct or site_events(settings.events)[event])
    in_app = direct or site_events(settings.app_events)[event]
    if not (by_mail or in_app):
        return

    for user in recipients:
        if not user.is_active or user.is_terminal:
            continue
        mail = by_mail and bool(user.email) and (direct or user_wants(user, event))
        app = in_app and (direct or user_wants_app(user, event))
        if key:
            mail = mail and not NotificationLog.objects.filter(event=event, key=key, recipient=user).exists()
            app = app and not Notification.objects.filter(event=event, key=key, recipient=user).exists()
        if not (mail or app):
            continue
        with translation.override(user.language or "de"):
            subject, body = render(user)
        if app:
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
        if not mail:
            continue
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
