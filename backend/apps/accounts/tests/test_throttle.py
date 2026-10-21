from datetime import timedelta

from django.test import Client
from django.utils import timezone

from apps.accounts.models import SignInThrottle
from apps.accounts.services import throttle

from .test_two_factor import PASSWORD, enable_totp, login, verify


def test_wrong_passwords_lock_the_account_for_a_while(demo):
    client = Client()
    for _i in range(throttle.PASSWORD_LIMIT):
        assert login(client, password="wrong").status_code == 401
    # From now on not even the right password is checked, under any spelling of the name.
    assert login(client).status_code == 429
    assert login(Client(), username="EMPLOYEE").status_code == 429
    # Other accounts are not affected.
    assert login(Client(), username="sales").status_code == 200

    SignInThrottle.objects.update(window_start=timezone.now() - throttle.WINDOW - timedelta(1))
    assert login(client).status_code == 200


def test_successful_sign_in_resets_the_count(demo):
    client = Client()
    for _i in range(throttle.PASSWORD_LIMIT - 1):
        login(client, password="wrong")
    assert login(client).status_code == 200
    assert not SignInThrottle.objects.filter(key=throttle.password_key("employee")).exists()


def test_wrong_codes_count_across_new_sign_ins(employee_client):
    _secret, backup_codes = enable_totp(employee_client)
    attacker = Client()
    wrong = 0
    while wrong < throttle.CODE_LIMIT:
        assert login(attacker).status_code == 202
        # The per-sign-in limit sends the attacker back to the password, but the
        # account keeps counting.
        for _i in range(5):
            if wrong == throttle.CODE_LIMIT:
                break
            assert verify(attacker, "000000").status_code in (400, 401)
            wrong += 1
    assert login(attacker).status_code == 202
    assert verify(attacker, backup_codes[0]).status_code == 429
    # The second step has to start over with the password.
    assert verify(attacker, backup_codes[0]).status_code == 401


def test_correct_code_resets_the_code_count(employee_client):
    _secret, backup_codes = enable_totp(employee_client)
    client = Client()
    assert login(client).status_code == 202
    assert verify(client, "000000").status_code == 400
    assert verify(client, backup_codes[0]).status_code == 200
    assert not SignInThrottle.objects.filter(key__startswith="code:").exists()


def test_password_confirmation_is_limited_too(employee_client):
    for _i in range(throttle.PASSWORD_LIMIT):
        response = employee_client.post(
            "/api/auth/two-factor/disable", {"password": "wrong"}, content_type="application/json"
        )
        assert response.status_code == 403
    response = employee_client.post(
        "/api/auth/two-factor/disable", {"password": PASSWORD}, content_type="application/json"
    )
    assert response.status_code == 429
