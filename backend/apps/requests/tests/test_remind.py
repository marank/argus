from datetime import timedelta

from django.core import mail
from django.utils import timezone

from apps.accounts.models import User
from apps.requests.models import AssetRequest

from .flow import handed_out, laptops, prepare


def remind(client, rid):
    return client.post(f"/api/requests/{rid}/remind")


def test_remind_mails_the_employee_and_records_it(
    mail_on,
    employee_client,
    it_client,
    django_capture_on_commit_callbacks,
):
    rid = handed_out(employee_client, it_client)
    AssetRequest.objects.filter(pk=rid).update(end_date=timezone.localdate() - timedelta(days=2))
    mail.outbox.clear()
    with django_capture_on_commit_callbacks(execute=True):
        response = remind(it_client, rid)
    assert response.status_code == 200, response.content
    data = response.json()
    assert data["reminded_at"] is not None
    assert data["reminded_by"]["username"] == "it"
    requester = AssetRequest.objects.get(pk=rid).requester
    assert [message.to for message in mail.outbox] == [[requester.email]]
    assert "überfällig" in mail.outbox[0].subject  # the demo employee uses German


def test_remind_ignores_the_personal_switch(
    mail_on,
    employee_client,
    it_client,
    django_capture_on_commit_callbacks,
):
    rid = handed_out(employee_client, it_client)
    requester = AssetRequest.objects.get(pk=rid).requester
    requester.notification_settings = {"return_overdue": False, "return_reminder": False}
    requester.save()
    mail.outbox.clear()
    with django_capture_on_commit_callbacks(execute=True):
        assert remind(it_client, rid).status_code == 200
    assert len(mail.outbox) == 1


def test_remind_can_be_repeated(
    mail_on,
    employee_client,
    it_client,
    django_capture_on_commit_callbacks,
):
    rid = handed_out(employee_client, it_client)
    mail.outbox.clear()
    with django_capture_on_commit_callbacks(execute=True):
        remind(it_client, rid)
        remind(it_client, rid)
    assert len(mail.outbox) == 2


def test_remind_needs_mail(employee_client, it_client):
    rid = handed_out(employee_client, it_client)
    response = remind(it_client, rid)
    assert response.status_code == 409
    assert AssetRequest.objects.get(pk=rid).reminded_at is None


def test_remind_needs_an_email_address(mail_on, employee_client, it_client):
    rid = handed_out(employee_client, it_client)
    User.objects.filter(asset_requests__pk=rid).update(email="")
    assert remind(it_client, rid).status_code == 409


def test_remind_needs_lent_devices(mail_on, employee_client, it_client):
    rid = prepare(employee_client, it_client, laptops())
    assert remind(it_client, rid).status_code == 409
    rid = handed_out(employee_client, it_client, duration="permanent")
    assert remind(it_client, rid).status_code == 409
