"""Limits on wrong passwords and second-step codes, per account and across sessions.

Every attempt is counted before it is checked and the count is cleared after a
success, so parallel requests cannot try more than the limit. A fresh login or a
new email code does not reset it; only the end of the window does.
"""

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.http import HttpRequest
from django.utils import timezone

from apps.accounts.models import SignInThrottle, User

WINDOW = timedelta(minutes=15)
PASSWORD_LIMIT = 10
CODE_LIMIT = 10
# Wrong passwords per client address, whichever accounts they try. Generous, since
# several people may sign in from behind one address.
ADDRESS_LIMIT = 30


def password_key(username: str) -> str:
    # Usernames ignore case, so "Admin" and "admin" share one count.
    return f"password:{username.strip().lower()[:150]}"


def code_key(user: User) -> str:
    return f"code:{user.pk}"


def address_key(request: HttpRequest) -> str:
    return f"address:{client_address(request)}"


def client_address(request: HttpRequest) -> str:
    """The client's IP address; behind nginx from X-Real-IP, which nginx always sets."""
    real_ip = request.META.get("HTTP_X_REAL_IP")
    if settings.BEHIND_PROXY and real_ip:
        return str(real_ip)
    return str(request.META.get("REMOTE_ADDR", ""))


def attempt(key: str, limit: int) -> bool:
    """Counts one attempt; False when ``limit`` attempts were already made in the window."""
    # Counts of past windows are no longer needed (and would pile up for made-up usernames).
    SignInThrottle.objects.filter(window_start__lt=timezone.now() - WINDOW).delete()
    SignInThrottle.objects.get_or_create(key=key)
    with transaction.atomic():
        row = SignInThrottle.objects.select_for_update().get(key=key)
        now = timezone.now()
        if now - row.window_start >= WINDOW:
            row.failures, row.window_start = 0, now
        if row.failures >= limit:
            return False
        row.failures += 1
        row.save(update_fields=["failures", "window_start"])
    return True


def clear(key: str) -> None:
    SignInThrottle.objects.filter(key=key).delete()


def refund(key: str) -> None:
    """Takes back one attempt that succeeded (for counts shared by several accounts)."""
    SignInThrottle.objects.filter(key=key, failures__gt=0).update(failures=F("failures") - 1)
