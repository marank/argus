import ast
import os
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


def load_settings(show="DEBUG", **env) -> subprocess.CompletedProcess:
    """Imports the settings in a fresh interpreter with only ``env`` set and prints ``show``."""
    clean = {k: v for k, v in os.environ.items() if k not in {"SECRET_KEY", "DEBUG", "APP_URLS"}}
    return subprocess.run(
        [sys.executable, "-c", f"from config import settings; print(settings.{show})"],
        cwd=BACKEND,
        env=clean | env,
        capture_output=True,
        text=True,
    )


def test_debug_is_on_only_without_a_secret_key():
    assert load_settings().stdout.strip() == "True"
    assert load_settings(SECRET_KEY=STRONG_KEY).stdout.strip() == "False"
    assert load_settings(SECRET_KEY=STRONG_KEY, DEBUG="true").stdout.strip() == "True"


def test_app_urls_with_ip_addresses_are_allowed_hosts():
    urls = "http://192.168.1.10:8080,https://[FD00::1]:8443"
    env = {"APP_URLS": urls, "SECRET_KEY": STRONG_KEY}
    hosts = ast.literal_eval(load_settings("ALLOWED_HOSTS", **env).stdout)
    origins = ast.literal_eval(load_settings("CSRF_TRUSTED_ORIGINS", **env).stdout)

    for host in ("192.168.1.10:8080", "[fd00::1]:8443"):
        assert validate_host(split_domain_port(host)[0], hosts)
    assert origins == ["http://192.168.1.10:8080", "https://[fd00::1]:8443"]


@pytest.mark.parametrize("key",["change-me", "short-but-not-a-placeholder", "django-insecure-" + "x" * 40])
def test_weak_secret_keys_are_refused_without_debug(key):
    result = load_settings(SECRET_KEY=key)
    assert result.returncode != 0
    assert "ImproperlyConfigured" in result.stderr


def test_initial_administrator_takes_any_password(db, monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "root")
    monkeypatch.setenv("ADMIN_PASSWORD", "123")
    call_command("ensure_superuser", stdout=StringIO())
    root = User.objects.get(username="root")
    assert root.is_superuser and root.check_password("123")


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
