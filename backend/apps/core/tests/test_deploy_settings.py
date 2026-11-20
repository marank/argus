import json
import subprocess
import sys
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.http.request import split_domain_port, validate_host

from apps.accounts.models import SignInThrottle, TwoFactor, User
from apps.accounts.services import throttle, two_factor

BACKEND = Path(__file__).resolve().parents[3]
STRONG_KEY = "x" * 20 + "a-long-random-looking-test-key"


APP_URLS = "http://192.168.1.10:8080,https://[FD00::1]:8443"
WEAK_KEYS = ["change-me", "short-but-not-a-placeholder", "django-insecure-" + "x" * 40]
ENVIRONMENTS = {
    "nothing": {},
    "debug": {"DEBUG": "true"},
    "secret key": {"SECRET_KEY": STRONG_KEY},
    "secret key and debug": {"SECRET_KEY": STRONG_KEY, "DEBUG": "true"},
    "empty debug": {"SECRET_KEY": STRONG_KEY, "DEBUG": ""},
    "misspelt debug": {"SECRET_KEY": STRONG_KEY, "DEBUG": "ture"},
    "bad port": {"SECRET_KEY": STRONG_KEY, "DB_HOST": "db", "DB_PORT": "five"},
    "bad backup time": {"SECRET_KEY": STRONG_KEY, "BACKUP_TIME": "1:30 am"},
    "app urls": {"SECRET_KEY": STRONG_KEY, "APP_URLS": APP_URLS},
} | {f"weak key {key}": {"SECRET_KEY": key} for key in WEAK_KEYS}

# Imports the settings once per environment, all in one fresh interpreter (starting
# one per case took seconds each), and prints what each import gave as JSON.
LOAD_EACH = """
import importlib, json, os, sys
names = {"SECRET_KEY", "DEBUG", "APP_URLS", "DB_HOST", "DB_PORT", "BACKUP_TIME"}
base = {k: v for k, v in os.environ.items() if k not in names}
results = {}
for name, env in json.loads(sys.argv[1]).items():
    os.environ.clear()
    os.environ.update(base | env)
    sys.modules.pop("config.settings", None)
    try:
        settings = importlib.import_module("config.settings")
    except Exception as error:
        results[name] = {"error": type(error).__name__}
    else:
        results[name] = {k: getattr(settings, k) for k in ("DEBUG", "ALLOWED_HOSTS", "CSRF_TRUSTED_ORIGINS")}
print(json.dumps(results))
"""


@pytest.fixture(scope="module")
def loaded():
    result = subprocess.run(
        [sys.executable, "-c", LOAD_EACH, json.dumps(ENVIRONMENTS)],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def test_debug_is_on_only_when_set(loaded):
    assert loaded["debug"]["DEBUG"] is True
    assert loaded["secret key"]["DEBUG"] is False
    assert loaded["empty debug"]["DEBUG"] is False
    assert loaded["secret key and debug"]["DEBUG"] is True


def test_without_secret_key_and_debug_argus_does_not_start(loaded):
    assert loaded["nothing"] == {"error": "ImproperlyConfigured"}


@pytest.mark.parametrize("case", ["misspelt debug", "bad port", "bad backup time"])
def test_invalid_values_stop_the_start(loaded, case):
    assert loaded[case] == {"error": "ImproperlyConfigured"}


def test_app_urls_with_ip_addresses_are_allowed_hosts(loaded):
    hosts = loaded["app urls"]["ALLOWED_HOSTS"]
    for host in ("192.168.1.10:8080", "[fd00::1]:8443"):
        assert validate_host(split_domain_port(host)[0], hosts)
    assert loaded["app urls"]["CSRF_TRUSTED_ORIGINS"] == [
        "http://192.168.1.10:8080",
        "https://[fd00::1]:8443",
    ]


@pytest.mark.parametrize("key", WEAK_KEYS)
def test_weak_secret_keys_are_refused_without_debug(loaded, key):
    assert loaded[f"weak key {key}"] == {"error": "ImproperlyConfigured"}


def test_initial_administrator_takes_any_password(db, monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "root")
    monkeypatch.setenv("ADMIN_PASSWORD", "123")
    call_command("ensure_superuser", stdout=StringIO())
    root = User.objects.get(username="root")
    assert root.is_superuser and root.check_password("123")


def test_initial_administrator_stays_an_administrator_but_not_active(db, monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "root")
    monkeypatch.setenv("ADMIN_PASSWORD", "first")
    call_command("ensure_superuser", stdout=StringIO())
    User.objects.filter(username="root").update(is_superuser=False, is_staff=False, is_active=False)

    monkeypatch.setenv("ADMIN_PASSWORD", "second")
    out = StringIO()
    call_command("ensure_superuser", stdout=out)
    root = User.objects.get(username="root")
    assert root.is_superuser and root.is_staff
    assert not root.is_active
    assert root.check_password("first")
    assert "deactivated" in out.getvalue()


def test_set_password_accepts_any_password_and_lifts_locks(demo):
    admin = User.objects.get(username="admin")
    TwoFactor.objects.create(user=admin, method="totp", totp_secret=two_factor.new_totp_secret())
    for key in (throttle.password_key("admin"), throttle.code_key(admin)):
        SignInThrottle.objects.create(key=key, failures=99)

    out = StringIO()
    call_command("set_password", "Admin", password="1", stdout=out)
    admin.refresh_from_db()
    assert admin.check_password("1")
    assert not SignInThrottle.objects.exists()
    assert "stays on" in out.getvalue()
    assert TwoFactor.objects.filter(user=admin).exists()

    call_command("set_password", "admin", password="2", reset_two_factor=True, stdout=StringIO())
    assert not TwoFactor.objects.filter(user=admin).exists()


def test_set_password_asks_twice_without_the_option(demo, monkeypatch):
    answers = iter(["neu", "anders"])
    monkeypatch.setattr("getpass.getpass", lambda prompt: next(answers))
    with pytest.raises(CommandError, match="do not match"):
        call_command("set_password", "admin", stdout=StringIO())
    with pytest.raises(CommandError, match="no account"):
        call_command("set_password", "nobody", password="x", stdout=StringIO())


def test_initial_administrator_matches_any_case(db, monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "root")
    monkeypatch.setenv("ADMIN_PASSWORD", "first")
    call_command("ensure_superuser", stdout=StringIO())

    monkeypatch.setenv("ADMIN_USERNAME", "Root")
    call_command("ensure_superuser", stdout=StringIO())
    assert User.objects.filter(username__iexact="root").count() == 1
