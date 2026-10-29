"""Background jobs, run by ``manage.py procrastinate worker`` (see ``apps.core.jobs``).

Mail texts are rendered when they are queued and only delivered here, in the HTML
layout and the recipient's language. Delivery reads the mail settings at send time,
so switching mail off also stops queued mails.
"""

from datetime import timedelta

from django.utils import timezone, translation
from procrastinate import RetryStrategy
from procrastinate.contrib.django import app

from apps.core.models import MailSettings, Notification, NotificationLog
from apps.core.notifications import EVENT_KEYS, link, mail_ready, send_mail
from apps.core.services.reminders import send_due_reminders

# Backs off from seconds to hours and gives up after about a day.
NOTIFICATION_RETRY = RetryStrategy(max_attempts=10, exponential_wait=3)


@app.task(queue="mail", retry=NOTIFICATION_RETRY)
def send_notification(
    *,
    event: str,
    to: str,
    subject: str,
    body: str,
    url: str = "",
    language: str = "de",
    key: str = "",
    recipient: str = "",
) -> None:
    """With ``key`` (reminders) the notification counts as sent only once it was delivered."""
    settings = MailSettings.load()
    if not mail_ready(settings):
        return
    # Kinds the recipient can switch off; mails sent on purpose by IT are not among them.
    manage_url = link(settings, "/profile/notifications") if event in EVENT_KEYS else ""
    with translation.override(language):
        send_mail(settings, to, subject, body, url=url, manage_url=manage_url)
    if key:
        NotificationLog.objects.get_or_create(event=event, key=key, recipient_id=recipient)


@app.periodic(cron="0 * * * *")
@app.task(queueing_lock="send_reminders")
def send_reminders(timestamp: int) -> None:
    send_due_reminders()


# Read in-app notifications are kept this long; unread ones stay until they are read.
READ_NOTIFICATIONS_KEPT = timedelta(days=90)


@app.periodic(cron="45 3 * * *")
@app.task(queueing_lock="remove_read_notifications")
def remove_read_notifications(timestamp: int) -> None:
    Notification.objects.filter(read_at__lt=timezone.now() - READ_NOTIFICATIONS_KEPT).delete()


@app.periodic(cron="30 3 * * *")
@app.task(pass_context=True)
async def remove_old_jobs(context, timestamp: int) -> None:
    """Finished jobs hold recipients and mail texts; keep them only briefly."""
    manager = context.app.job_manager
    await manager.delete_old_jobs(nb_hours=24)
    await manager.delete_old_jobs(
        nb_hours=14 * 24, include_failed=True, include_cancelled=True, include_aborted=True
    )
