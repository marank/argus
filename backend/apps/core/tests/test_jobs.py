import json
from datetime import timedelta

import pytest
from django.core import mail
from django.db import connection, transaction
from django.utils import timezone
from procrastinate.contrib.django import app

from apps.accounts.models import User
from apps.core import tasks
from apps.core.models import MailSettings, NotificationLog
from apps.core.services.reminders import send_due_reminders
from apps.requests.models import AssetRequest, AssetRequestStatus
from apps.requests.services import notifications as asset_request_notifications

postgres_only = pytest.mark.skipif(
    connection.vendor != "postgresql", reason="the job queue lives in PostgreSQL"
)


@pytest.fixture
def job_queue(settings):
    """Mails go through the Procrastinate queue, as in production (not the default in tests)."""
    settings.JOB_QUEUE = True


def queued() -> list[tuple[str, str]]:
    with connection.cursor() as cursor:
        cursor.execute("SELECT task_name, args FROM procrastinate_jobs WHERE status = 'todo' ORDER BY id")
        rows: list[tuple[str, str]] = cursor.fetchall()
        return rows


def run_jobs() -> None:
    """Works off the queue in-process, inside the test's transaction (a worker could not see it)."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, task_name, args FROM procrastinate_jobs WHERE status = 'todo' ORDER BY id")
        jobs = cursor.fetchall()
    for id, task_name, args in jobs:
        # Django leaves jsonb as text.
        app.tasks[task_name](**json.loads(args))
        with connection.cursor() as cursor:
            cursor.execute("UPDATE procrastinate_jobs SET status = 'succeeded' WHERE id = %s", [id])


def overdue_asset_request() -> AssetRequest:
    employee = User.objects.get(username="employee")
    today = timezone.localdate()
    return AssetRequest.objects.create(
        requester=employee,
        created_by=employee,
        title="Overdue",
        duration=AssetRequest.Duration.TEMPORARY,
        start_date=today - timedelta(days=10),
        end_date=today - timedelta(days=2),
        status=AssetRequestStatus.HANDED_OUT,
    )


@postgres_only
def test_a_notification_is_queued_and_delivered_by_the_job(mail_on, job_queue):
    asset_request = overdue_asset_request()
    asset_request_notifications.return_requested(asset_request, User.objects.get(username="it"))
    assert [name for name, _ in queued()] == ["apps.core.tasks.send_notification"]
    assert mail.outbox == []

    run_jobs()
    assert [message.to for message in mail.outbox] == [["employee@example.com"]]


@postgres_only
def test_a_rolled_back_change_queues_no_mail(mail_on, job_queue):
    asset_request = overdue_asset_request()

    def change_then_fail() -> None:
        with transaction.atomic():
            asset_request_notifications.return_requested(asset_request, User.objects.get(username="it"))
            assert len(queued()) == 1
            raise RuntimeError

    with pytest.raises(RuntimeError):
        change_then_fail()
    assert queued() == []


@postgres_only
def test_a_reminder_is_queued_once_and_counts_as_sent_after_delivery(mail_on, job_queue):
    overdue_asset_request()
    send_due_reminders()
    first = queued()
    # Still waiting (e.g. for a retry): the hourly run does not queue it again.
    send_due_reminders()
    assert queued() == first
    assert not NotificationLog.objects.filter(event="return_overdue").exists()

    run_jobs()
    assert NotificationLog.objects.filter(event="return_overdue").count() == 1
    # Delivered: not queued again.
    send_due_reminders()
    assert queued() == []


def test_a_failed_delivery_does_not_count_as_sent(mail_on, monkeypatch):
    employee = User.objects.get(username="employee")

    def refuse(*args, **kwargs):
        raise ConnectionRefusedError

    monkeypatch.setattr(tasks, "send_mail", refuse)
    with pytest.raises(ConnectionRefusedError):
        tasks.send_notification(
            event="return_overdue",
            to=employee.email,
            subject="s",
            body="b",
            key="k",
            recipient=str(employee.pk),
        )
    assert not NotificationLog.objects.exists()


def test_queued_mails_stay_unsent_once_mail_is_switched_off(mail_on):
    MailSettings.objects.update(enabled=False)
    tasks.send_notification(event="request_ready", to="employee@example.com", subject="s", body="b")
    assert mail.outbox == []
