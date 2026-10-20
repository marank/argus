import re
import time

import pytest
from django.core import mail
from django.test import Client

from apps.accounts.models import BackupCode, TwoFactor, User
from apps.accounts.services import two_factor
from apps.core.models import MailSettings

JSON = "application/json"
PASSWORD = "argus-demo"


@pytest.fixture
def mail_on(db):
    MailSettings.objects.update_or_create(
        defaults={"enabled": True, "host": "smtp.example.com", "from_email": "argus@example.com"}
    )


def login(client: Client, username="employee", password=PASSWORD):
    return client.post("/api/auth/login", {"username": username, "password": password}, content_type=JSON)


def verify(client: Client, code: str):
    return client.post("/api/auth/login/verify", {"code": code}, content_type=JSON)


def current_totp(secret: str) -> str:
    return two_factor.totp_code(secret, int(time.time()) // two_factor.TOTP_STEP)


def mailed_code() -> str:
    return re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)


def enable_totp(client: Client) -> tuple[str, list[str]]:
    setup = client.post(
        "/api/auth/two-factor/setup", {"method": "totp", "password": PASSWORD}, content_type=JSON
    )
    assert setup.status_code == 200, setup.content
    secret = setup.json()["secret"]
    assert setup.json()["qr_svg"].startswith("data:image/svg+xml")
    confirm = client.post(
        "/api/auth/two-factor/setup/confirm", {"code": current_totp(secret)}, content_type=JSON
    )
    assert confirm.status_code == 200, confirm.content
    return secret, confirm.json()["backup_codes"]


def test_totp_matches_rfc_6238_vector():
    # RFC 6238 appendix B, SHA-1, T = 59 s; the secret is "12345678901234567890".
    secret = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
    assert two_factor.totp_code(secret, 59 // 30) == "287082"


def test_login_without_two_factor_is_unchanged(demo):
    response = login(Client())
    assert response.status_code == 200
    assert response.json()["two_factor"] is None


def test_setup_needs_the_password(employee_client):
    response = employee_client.post(
        "/api/auth/two-factor/setup", {"method": "totp", "password": "wrong"}, content_type=JSON
    )
    assert response.status_code == 403
    assert not TwoFactor.objects.exists()


def test_wrong_setup_code_keeps_it_off(employee_client):
    employee_client.post(
        "/api/auth/two-factor/setup", {"method": "totp", "password": PASSWORD}, content_type=JSON
    )
    response = employee_client.post(
        "/api/auth/two-factor/setup/confirm", {"code": "000000"}, content_type=JSON
    )
    assert response.status_code == 400
    assert not TwoFactor.objects.exists()


def test_totp_login(employee_client):
    secret, codes = enable_totp(employee_client)
    assert len(codes) == two_factor.BACKUP_CODE_COUNT
    status = employee_client.get("/api/auth/two-factor").json()
    assert status == {**status, "method": "totp", "backup_codes_left": 10}

    client = Client()
    challenge = login(client)
    assert challenge.status_code == 202
    assert challenge.json()["two_factor"] == "totp"
    # Not signed in yet.
    assert client.get("/api/auth/me").status_code == 401

    # The code used for the setup cannot be used again; wait for the next one.
    user = User.objects.get(username="employee")
    step = user.two_factor.totp_last_step
    assert verify(client, two_factor.totp_code(secret, step)).status_code == 400
    assert verify(client, two_factor.totp_code(secret, step + 1)).status_code == 200
    assert client.get("/api/auth/me").json()["two_factor"] == "totp"


def test_backup_code_works_once(employee_client):
    _secret, codes = enable_totp(employee_client)

    client = Client()
    login(client)
    assert verify(client, codes[0].upper().replace("-", " ")).status_code == 200

    client = Client()
    login(client)
    assert verify(client, codes[0]).status_code == 400
    assert BackupCode.objects.filter(used_at__isnull=True).count() == 9


def test_too_many_wrong_codes_need_the_password_again(employee_client):
    enable_totp(employee_client)
    client = Client()
    login(client)
    for _i in range(two_factor.MAX_ATTEMPTS - 1):
        assert verify(client, "000000").status_code == 400
    assert verify(client, "000000").status_code == 401
    assert verify(client, "000000").status_code == 401


def test_verify_without_password_step_is_refused(demo):
    assert verify(Client(), "123456").status_code == 401


def test_email_login(employee_client, mail_on):
    employee = User.objects.get(username="employee")
    employee.email = "erika@example.com"
    employee.save()

    setup = employee_client.post(
        "/api/auth/two-factor/setup", {"method": "email", "password": PASSWORD}, content_type=JSON
    )
    assert setup.json()["code_sent"] is True
    assert setup.json()["email_hint"] == "e***@example.com"
    confirm = employee_client.post(
        "/api/auth/two-factor/setup/confirm", {"code": mailed_code()}, content_type=JSON
    )
    assert confirm.status_code == 200, confirm.content

    client = Client()
    challenge = login(client)
    assert challenge.status_code == 202
    assert challenge.json() == {"two_factor": "email", "email_hint": "e***@example.com", "code_sent": True}
    assert mail.outbox[-1].to == ["erika@example.com"]
    # Too early for another code.
    assert client.post("/api/auth/login/resend", content_type=JSON).status_code == 429
    assert verify(client, mailed_code()).status_code == 200


def test_email_method_needs_mail(employee_client):
    response = employee_client.post(
        "/api/auth/two-factor/setup", {"method": "email", "password": PASSWORD}, content_type=JSON
    )
    assert response.status_code == 409


def test_disable_and_new_backup_codes(employee_client):
    _secret, old = enable_totp(employee_client)
    renewed = employee_client.post(
        "/api/auth/two-factor/backup-codes", {"password": PASSWORD}, content_type=JSON
    )
    assert renewed.status_code == 200
    assert set(renewed.json()["backup_codes"]).isdisjoint(old)

    assert (
        employee_client.post(
            "/api/auth/two-factor/disable", {"password": "wrong"}, content_type=JSON
        ).status_code
        == 403
    )
    assert (
        employee_client.post(
            "/api/auth/two-factor/disable", {"password": PASSWORD}, content_type=JSON
        ).status_code
        == 204
    )
    assert not BackupCode.objects.exists()
    assert login(Client()).status_code == 200


def test_it_resets_two_factor(employee_client, it_client):
    enable_totp(employee_client)
    employee = User.objects.get(username="employee")

    users = it_client.get("/api/accounts/users", {"q": "employee"}).json()["items"]
    assert next(u for u in users if u["username"] == "employee")["two_factor"] == "totp"

    response = it_client.post(f"/api/accounts/users/{employee.pk}/two-factor/reset", content_type=JSON)
    assert response.status_code == 200
    assert response.json()["two_factor"] is None
    assert login(Client()).status_code == 200


def test_employees_cannot_reset_or_see_two_factor(employee_client, it_client):
    it = User.objects.get(username="it")
    TwoFactor.objects.create(user=it, method="totp", totp_secret=two_factor.new_totp_secret())
    assert employee_client.post(f"/api/accounts/users/{it.pk}/two-factor/reset").status_code == 403
    assert employee_client.get(f"/api/accounts/users/{it.pk}").json()["two_factor"] is None


def test_it_cannot_reset_an_administrator(it_client):
    admin = User.objects.get(username="admin")
    TwoFactor.objects.create(user=admin, method="totp", totp_secret=two_factor.new_totp_secret())
    assert it_client.post(f"/api/accounts/users/{admin.pk}/two-factor/reset").status_code == 403
    assert TwoFactor.objects.filter(user=admin).exists()


def test_admin_login_goes_through_the_app(db):
    response = Client().get("/admin/login/?next=/admin/accounts/user/")
    assert response.status_code == 302
    assert response["Location"] == "/login?next=%2Fadmin%2Faccounts%2Fuser%2F"
    assert (
        Client().get("/admin/login/?next=https://evil.example").headers["Location"]
        == "/login?next=%2Fadmin%2F"
    )
