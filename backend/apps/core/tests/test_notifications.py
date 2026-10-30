from datetime import date, timedelta
from typing import TYPE_CHECKING

import pytest
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.core.management import call_command
from django.test import Client
from django.utils import timezone

from apps.accounts.models import User
from apps.core.models import MailSettings, SiteSettings
from apps.masterdata.models import Category
from apps.requests.models import AssetRequest, AssetRequestStatus

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse

JSON = "application/json"


@pytest.fixture
def mail_on(demo):
    settings = MailSettings.load()
    settings.enabled = True
    settings.host = "smtp.example.com"
    settings.from_email = "argus@example.com"
    settings.app_url = "https://argus.example.com"
    settings.save()
    return settings


def submit(client: Client, days: int = 3) -> _MonkeyPatchedWSGIResponse:
    start = date.today() + timedelta(days=1)
    response = client.post(
        "/api/requests",
        {
            "title": "Workshop",
            "duration": "temporary",
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(days=days - 1)).isoformat(),
            "items": [{"category": str(Category.objects.get(code="headsets").pk), "quantity": 1}],
        },
        content_type=JSON,
    )
    return response


def recipients() -> set[str]:
    return {address for message in mail.outbox for address in message.to}


def test_new_request_notifies_it(mail_on, employee_client, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        assert submit(employee_client).status_code == 201
    staff = set(User.objects.filter(is_staff=True, is_terminal=False).values_list("email", flat=True))
    assert recipients() == staff
    assert "https://argus.example.com/requests/" in mail.outbox[0].body


def test_mails_come_in_the_app_layout_too(mail_on, employee_client, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        submit(employee_client)
    message = mail.outbox[0]
    assert isinstance(message, EmailMultiAlternatives)
    html, mimetype = message.alternatives[0]
    assert isinstance(html, str)
    assert mimetype == "text/html"
    assert 'href="https://argus.example.com/requests/' in html
    assert "https://argus.example.com/profile/notifications" in html
    assert "Workshop" in html
    # The logo travels with the HTML part, not as an attachment.
    parts = [part.get_content_type() for part in message.message().walk()]
    assert parts == ["multipart/alternative", "text/plain", "multipart/related", "text/html", "image/png"]


def test_mail_blocks():
    from apps.core.notifications import blocks

    assert blocks("Ready.\n\nStill to return:\n- A\n- B\n\nCode 123456 here.\n\nBye", "123456") == [
        {"text": "Ready."},
        {"label": "Still to return", "lines": ["A", "B"]},
        {"text": "Code 123456 here."},
        {"code": "123456"},
        {"text": "Bye"},
    ]


def test_decision_goes_to_requester_in_their_language(
    mail_on, employee_client, it_client, django_capture_on_commit_callbacks
):
    asset_request = submit(employee_client).json()
    mail.outbox.clear()
    with django_capture_on_commit_callbacks(execute=True):
        it_client.post(f"/api/requests/{asset_request['id']}/confirm", {"items": []}, content_type=JSON)
    assert recipients() == {"employee@example.com"}
    assert "bestätigt" in mail.outbox[0].subject  # the demo employee uses German


def test_users_and_admins_can_switch_notifications_off(
    mail_on, employee_client, it_client, django_capture_on_commit_callbacks
):
    response = employee_client.patch(
        "/api/auth/me",
        {"notification_settings": {"request_confirmed": False, "unknown": False}},
        content_type=JSON,
    )
    assert response.json()["notification_settings"] == {"request_confirmed": False}

    asset_request = submit(employee_client).json()
    mail.outbox.clear()
    with django_capture_on_commit_callbacks(execute=True):
        it_client.post(f"/api/requests/{asset_request['id']}/confirm", {"items": []}, content_type=JSON)
    assert mail.outbox == []

    mail_on.events = {"request_submitted": False}
    mail_on.save()
    with django_capture_on_commit_callbacks(execute=True):
        submit(employee_client)
    assert mail.outbox == []


def test_nothing_is_sent_while_mail_is_off(demo, employee_client, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        submit(employee_client)
    assert mail.outbox == []


def test_reminders_are_sent_once(mail_on, django_capture_on_commit_callbacks):
    employee = User.objects.get(username="employee")
    today = timezone.localdate()
    for title, end in (("Due tomorrow", today + timedelta(days=1)), ("Overdue", today - timedelta(days=2))):
        AssetRequest.objects.create(
            requester=employee,
            created_by=employee,
            title=title,
            duration=AssetRequest.Duration.TEMPORARY,
            start_date=today - timedelta(days=10),
            end_date=end,
            status=AssetRequestStatus.HANDED_OUT,
        )
    with django_capture_on_commit_callbacks(execute=True):
        call_command("send_reminders", verbosity=0)
    first = len(mail.outbox)
    # One reminder (due tomorrow) and one overdue notice for the employee.
    assert len([m for m in mail.outbox if "employee@example.com" in m.to]) == 2
    # The AutoCAD license of the demo data ends within the warning period.
    assert any("AutoCAD" in m.subject for m in mail.outbox)

    with django_capture_on_commit_callbacks(execute=True):
        call_command("send_reminders", verbosity=0)
    assert len(mail.outbox) == first


def test_maximum_loan_period(demo, employee_client):
    site = SiteSettings.load()
    site.max_loan_days = 5
    site.save()
    assert submit(employee_client, days=6).status_code == 409
    assert submit(employee_client, days=5).status_code == 201


def test_mail_settings_keep_the_password_and_send_a_test(demo):
    admin = Client()
    admin.login(username="admin", password="argus-demo")
    payload = {
        "enabled": True,
        "host": "smtp.example.com",
        "port": 587,
        "security": "starttls",
        "username": "argus",
        "password": "secret",
        "from_email": "argus@example.com",
    }
    response = admin.put("/api/settings/mail", payload, content_type=JSON)
    assert response.status_code == 200, response.content
    assert response.json()["password_set"] is True
    assert "password" not in response.json()

    # Saving without a password keeps the stored one.
    response = admin.put("/api/settings/mail", {**payload, "password": None}, content_type=JSON)
    assert MailSettings.load().password == "secret"

    response = admin.post("/api/settings/mail/test", {"to": "admin@example.com"}, content_type=JSON)
    assert response.status_code == 200, response.content
    assert mail.outbox[-1].to == ["admin@example.com"]


def test_rules_are_part_of_the_site_settings(demo, employee_client):
    data = employee_client.get("/api/settings/site").json()
    assert data["rules"]["default_loan_days"] == 5
    assert {"key": "request_ready", "audience": "employee", "mail": True, "app": True} in data[
        "notifications"
    ]


@pytest.mark.parametrize("notify", [True, False])
def test_it_decides_whether_the_ready_message_goes_out(
    notify, mail_on, employee_client, it_client, django_capture_on_commit_callbacks
):
    url = f"/api/requests/{submit(employee_client).json()['id']}"
    it_client.post(f"{url}/confirm", {"items": []}, content_type=JSON)
    it_client.post(f"{url}/auto-allocate")
    mail.outbox.clear()
    with django_capture_on_commit_callbacks(execute=True):
        response = it_client.post(
            f"{url}/ready", {"handover_mode": "collect", "notify": notify}, content_type=JSON
        )
    assert response.status_code == 200, response.content
    assert (recipients() == {"employee@example.com"}) is notify
    ready = next(e for e in response.json()["events"] if e["kind"] == "ready")
    assert ready["data"].get("notified", True) is notify


def _ready(employee_client, it_client) -> str:
    url = f"/api/requests/{submit(employee_client).json()['id']}"
    it_client.post(f"{url}/confirm", {"items": []}, content_type=JSON)
    it_client.post(f"{url}/auto-allocate")
    it_client.post(f"{url}/ready", {"handover_mode": "collect", "notify": False}, content_type=JSON)
    return url


def test_the_employee_hears_of_every_step_after_ready(
    mail_on, employee_client, it_client, django_capture_on_commit_callbacks
):
    """Changed handover, hand-out, extension and return: each one mail for the record."""
    url = _ready(employee_client, it_client)
    steps = [
        ("schedule", {"handover_mode": "delivery", "pickup_location": None}, "Übergabe geändert"),
        ("hand-out", {}, "Ausgegeben"),
        ("extend", {"end_date": (date.today() + timedelta(days=20)).isoformat()}, "Leihfrist verlängert"),
        ("return", {}, "Zurückgenommen"),
    ]
    for action, data, subject in steps:
        mail.outbox.clear()
        with django_capture_on_commit_callbacks(execute=True):
            response = it_client.post(f"{url}/{action}", data, content_type=JSON)
        assert response.status_code == 200, response.content
        assert recipients() == {"employee@example.com"}, action
        assert subject in mail.outbox[0].subject
    assert "HS-" in mail.outbox[0].body  # the devices, by inventory number


def test_a_changed_handover_can_go_unannounced(
    mail_on, employee_client, it_client, django_capture_on_commit_callbacks
):
    url = _ready(employee_client, it_client)
    mail.outbox.clear()
    with django_capture_on_commit_callbacks(execute=True):
        body = it_client.post(
            f"{url}/schedule", {"handover_mode": "delivery", "notify": False}, content_type=JSON
        ).json()
    assert mail.outbox == []
    assert body["events"][-1]["data"]["notified"] is False


def test_only_a_cancellation_by_it_is_mailed(
    mail_on, employee_client, it_client, django_capture_on_commit_callbacks
):
    own = submit(employee_client).json()["id"]
    by_it = submit(employee_client).json()["id"]
    mail.outbox.clear()
    with django_capture_on_commit_callbacks(execute=True):
        employee_client.post(f"/api/requests/{own}/cancel")
    assert mail.outbox == []
    with django_capture_on_commit_callbacks(execute=True):
        it_client.post(f"/api/requests/{by_it}/cancel")
    assert recipients() == {"employee@example.com"}
    assert "storniert" in mail.outbox[0].subject


def test_new_kinds_follow_the_site_and_personal_switches(
    mail_on, employee_client, it_client, django_capture_on_commit_callbacks
):
    url = _ready(employee_client, it_client)
    employee_client.patch(
        "/api/auth/me", {"notification_settings": {"request_handed_out": False}}, content_type=JSON
    )
    mail.outbox.clear()
    with django_capture_on_commit_callbacks(execute=True):
        it_client.post(f"{url}/hand-out", {}, content_type=JSON)
    assert mail.outbox == []

    mail_on.events = {"request_returned": False}
    mail_on.save()
    with django_capture_on_commit_callbacks(execute=True):
        it_client.post(f"{url}/return", {}, content_type=JSON)
    assert mail.outbox == []


def test_only_mails_one_can_get_can_be_switched_off(employee_client, it_client):
    """An employee's profile takes no switches for IT mails; IT staff may turn off their own."""
    data = {"notification_settings": {"request_ready": False, "request_submitted": False}}
    response = employee_client.patch("/api/auth/me", data, content_type=JSON)
    assert response.json()["notification_settings"] == {"request_ready": False}

    response = it_client.patch("/api/auth/me", data, content_type=JSON)
    assert response.json()["notification_settings"] == {"request_ready": False, "request_submitted": False}


# --- In the app ----------------------------------------------------------------


@pytest.fixture(autouse=True)
def empty_bell(request):
    """The demo data rings the bell itself; the in-app tests start from an empty one."""
    if "demo" in request.fixturenames:
        from apps.core.models import Notification

        request.getfixturevalue("demo")
        Notification.objects.all().delete()


def _confirm(employee_client, it_client, django_capture_on_commit_callbacks) -> str:
    rid: str = submit(employee_client).json()["id"]
    mail.outbox.clear()
    with django_capture_on_commit_callbacks(execute=True):
        it_client.post(f"/api/requests/{rid}/confirm", {"items": []}, content_type=JSON)
    return rid


def test_the_bell_works_without_a_mail_server(
    demo, employee_client, it_client, django_capture_on_commit_callbacks
):
    rid = _confirm(employee_client, it_client, django_capture_on_commit_callbacks)
    assert mail.outbox == []
    assert employee_client.get("/api/notifications/unread").json() == {"unread": 1}
    (item,) = employee_client.get("/api/notifications").json()["items"]
    assert item["event"] == "request_confirmed"
    assert "bestätigt" in item["title"]  # in the recipient's language, like the email
    assert item["path"] == f"/portal/requests/{rid}"
    assert "\n" not in item["text"]  # only what happened, not the item list

    read = employee_client.post(f"/api/notifications/{item['id']}/read").json()
    assert read["read_at"] is not None
    assert employee_client.get("/api/notifications/unread").json() == {"unread": 0}
    # Nobody else's.
    assert it_client.post(f"/api/notifications/{item['id']}/read").status_code == 404


def test_each_channel_has_its_own_switches(
    mail_on, employee_client, it_client, django_capture_on_commit_callbacks
):
    employee_client.patch(
        "/api/auth/me", {"app_notification_settings": {"request_confirmed": False}}, content_type=JSON
    )
    _confirm(employee_client, it_client, django_capture_on_commit_callbacks)
    assert recipients() == {"employee@example.com"}
    assert employee_client.get("/api/notifications/unread").json() == {"unread": 0}

    mail_on.events = {"request_confirmed": False}
    mail_on.save()
    employee_client.patch("/api/auth/me", {"app_notification_settings": {}}, content_type=JSON)
    _confirm(employee_client, it_client, django_capture_on_commit_callbacks)
    assert mail.outbox == []
    assert employee_client.get("/api/notifications/unread").json() == {"unread": 1}

    mail_on.app_events = {"request_confirmed": False}
    mail_on.save()
    _confirm(employee_client, it_client, django_capture_on_commit_callbacks)
    assert employee_client.get("/api/notifications/unread").json() == {"unread": 1}


def test_a_reminder_shows_once(demo, employee_client):
    from apps.core.notifications import NotificationEvent, notify

    employee = User.objects.get(username="employee")
    for _ in range(2):
        notify(
            NotificationEvent.RETURN_REMINDER,
            [employee],
            lambda user: ("Reminder", "Bring it back."),
            key="r:1",
        )
    assert employee_client.get("/api/notifications/unread").json() == {"unread": 1}


def test_read_all(demo, employee_client, it_client, django_capture_on_commit_callbacks):
    for _ in range(2):
        _confirm(employee_client, it_client, django_capture_on_commit_callbacks)
    assert employee_client.get("/api/notifications?unread=true").json()["count"] == 2
    assert employee_client.post("/api/notifications/read-all").json() == {"unread": 0}
    assert employee_client.get("/api/notifications").json()["count"] == 2


def test_site_wide_switches_per_channel(demo):
    admin = Client()
    admin.login(username="admin", password="argus-demo")
    data = {"mail": {"request_ready": False, "unknown": False}, "app": {"license_expiring": False}}
    body = admin.put("/api/settings/notifications", data, content_type=JSON).json()
    assert body["mail"]["request_ready"] is False and body["app"]["request_ready"] is True
    assert body["app"]["license_expiring"] is False and "unknown" not in body["mail"]
    assert Client().get("/api/settings/notifications").status_code in (401, 403)
