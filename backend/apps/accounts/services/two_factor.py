"""Two-factor sign-in: a code from an authenticator app (TOTP) or by email, plus backup codes.

After the password the login only remembers the user in the session
(``PENDING_LOGIN``); the session becomes a signed-in one once the second code
fits. Codes sent by email and secrets of a setup in progress live in the
(server-side) session too, so nothing is stored for the user before they
confirm. Each pending code allows a few attempts; after that the password has
to be entered again.
"""

import base64
import hashlib
import hmac
import logging
import secrets
import struct
import time
from typing import NotRequired, TypedDict
from urllib.parse import quote

import segno
from django.contrib.sessions.backends.base import SessionBase
from django.db import transaction
from django.utils import timezone, translation
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.translation import gettext as _

from apps.accounts.models import BackupCode, TwoFactor, TwoFactorMethod, User
from apps.core.models import MailSettings
from apps.core.notifications import mail_ready, send_mail

logger = logging.getLogger(__name__)

ISSUER = "Argus"
TOTP_STEP = 30  # seconds
TOTP_DIGITS = 6
EMAIL_CODE_TTL = 10 * 60
EMAIL_RESEND_AFTER = 30
PENDING_TTL = 10 * 60
MAX_ATTEMPTS = 5
BACKUP_CODE_COUNT = 10
# No 0/o, 1/l/i: backup codes are often typed from paper.
BACKUP_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"
BACKUP_CODE_LENGTH = 12

PENDING_LOGIN = "argus_2fa_login"
PENDING_SETUP = "argus_2fa_setup"


class PendingState(TypedDict):
    """A pending login or setup in the session, with the email code sent for it (hashed)."""

    expires: float
    attempts: int
    code: NotRequired[str]
    code_expires: NotRequired[float]
    code_sent: NotRequired[float]


class LoginState(PendingState):
    user: str  # id
    backend: str


class SetupState(PendingState):
    method: str
    secret: NotRequired[str]


class LoginChallenge(TypedDict):
    two_factor: str
    email_hint: str
    code_sent: bool


class SetupResult(TypedDict):
    method: str
    # Authenticator app
    secret: NotRequired[str]
    uri: NotRequired[str]
    qr_svg: NotRequired[str]
    # Email
    email_hint: NotRequired[str]
    code_sent: NotRequired[bool]


def method_of(user: User) -> str | None:
    two_factor = TwoFactor.objects.filter(user=user).first()
    return two_factor.method if two_factor else None


def email_available(user: User) -> bool:
    """Whether codes by email can reach the user right now."""
    return bool(user.email) and mail_ready(MailSettings.load())


def email_hint(address: str) -> str:
    """``m***@example.com``: enough to recognise the address, not to learn it."""
    name, _sep, domain = address.partition("@")
    return f"{name[:1]}***@{domain}" if domain else "***"


# --- Authenticator app (RFC 6238, SHA-1, 6 digits, 30 s) ---


def new_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode()


def totp_code(secret: str, step: int) -> str:
    digest = hmac.new(base64.b32decode(secret), struct.pack(">Q", step), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    number = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(number % 10**TOTP_DIGITS).zfill(TOTP_DIGITS)


def match_totp(secret: str, code: str, after_step: int = 0) -> int | None:
    """The time step ``code`` belongs to (one step of clock drift either way), or None."""
    now = int(time.time()) // TOTP_STEP
    for step in (now - 1, now, now + 1):
        if step > after_step and constant_time_compare(totp_code(secret, step), code):
            return step
    return None


def provisioning_uri(secret: str, user: User) -> str:
    label = quote(f"{ISSUER}:{user.username}")
    return f"otpauth://totp/{label}?secret={secret}&issuer={quote(ISSUER)}&digits={TOTP_DIGITS}&period={TOTP_STEP}"


def qr_svg(uri: str) -> str:
    """The setup link as an SVG data URI for authenticator apps to scan."""
    return segno.make(uri, error="m").svg_data_uri(scale=5, border=2, dark="#000", light="#fff")


# --- Codes by email ---


def _hash_code(purpose: str, code: str) -> str:
    return salted_hmac(f"argus.two_factor.{purpose}", code, algorithm="sha256").hexdigest()


def new_email_code() -> str:
    return str(secrets.randbelow(10**TOTP_DIGITS)).zfill(TOTP_DIGITS)


def send_email_code(user: User, code: str) -> bool:
    """Mails ``code`` right away; False when it could not be sent.

    Not a background job: the user waits for the code and should learn at once
    when it did not go out, and the code must not end up in the job table.
    """
    settings = MailSettings.load()
    if not (user.email and mail_ready(settings)):
        return False
    with translation.override(user.language or "de"):
        subject = _("Your Argus sign-in code: %(code)s") % {"code": code}
        body = _(
            "Hello %(name)s,\n\nyour code for signing in to Argus is %(code)s. "
            "It is valid for %(minutes)s minutes.\n\n"
            "If you did not initiate this sign-in, your password may be compromised: "
            "change it immediately and inform IT."
        ) % {"name": user.first_name or user.username, "code": code, "minutes": EMAIL_CODE_TTL // 60}
        try:
            send_mail(settings, user.email, subject, body, code=code)
        except Exception:  # noqa: BLE001 - the user is told the code did not go out
            logger.exception("Could not send sign-in code to %s", user.email)
            return False
    return True


def issue_email_code(state: PendingState, user: User) -> bool:
    """Puts a fresh email code into ``state`` (a pending login or setup) and sends it."""
    code = new_email_code()
    state["code"] = _hash_code("email", code)
    state["code_expires"] = time.time() + EMAIL_CODE_TTL
    state["code_sent"] = time.time()
    state["attempts"] = 0
    return send_email_code(user, code)


def can_resend(state: PendingState) -> bool:
    return time.time() - state.get("code_sent", 0) >= EMAIL_RESEND_AFTER


def match_email_code(state: PendingState, code: str) -> bool:
    return (
        bool(state.get("code"))
        and time.time() < state.get("code_expires", 0)
        and constant_time_compare(state["code"], _hash_code("email", code))
    )


# --- Backup codes ---


def normalize(code: str) -> str:
    return "".join(c for c in code.lower() if c.isalnum())


def _hash_backup(salt: str, code: str) -> str:
    return hashlib.sha256(f"{salt}:{normalize(code)}".encode()).hexdigest()


def format_backup_code(code: str) -> str:
    return "-".join(code[i : i + 4] for i in range(0, len(code), 4))


@transaction.atomic
def new_backup_codes(user: User) -> list[str]:
    """Replaces all backup codes of ``user``; the plain codes are only returned here."""
    BackupCode.objects.filter(user=user).delete()
    codes = []
    for _i in range(BACKUP_CODE_COUNT):
        code = "".join(secrets.choice(BACKUP_ALPHABET) for _j in range(BACKUP_CODE_LENGTH))
        salt = secrets.token_hex(16)
        BackupCode.objects.create(user=user, salt=salt, code_hash=_hash_backup(salt, code))
        codes.append(format_backup_code(code))
    return codes


def backup_codes_left(user: User) -> int:
    return BackupCode.objects.filter(user=user, used_at__isnull=True).count()


def use_backup_code(user: User, code: str) -> bool:
    if len(normalize(code)) != BACKUP_CODE_LENGTH:
        return False
    for backup in BackupCode.objects.filter(user=user, used_at__isnull=True):
        if constant_time_compare(backup.code_hash, _hash_backup(backup.salt, code)):
            # Only one request may spend the code.
            return bool(
                BackupCode.objects.filter(pk=backup.pk, used_at__isnull=True).update(used_at=timezone.now())
            )
    return False


# --- Signing in ---


def start_login(session: SessionBase, user: User, two_factor: TwoFactor) -> LoginChallenge:
    """Remembers ``user`` until the second step; returns the challenge for the frontend."""
    state: LoginState = {
        "user": str(user.pk),
        "backend": user.backend,
        "expires": time.time() + PENDING_TTL,
        "attempts": 0,
    }
    sent = False
    if two_factor.method == TwoFactorMethod.EMAIL:
        sent = issue_email_code(state, user)
    session[PENDING_LOGIN] = state
    return {
        "two_factor": two_factor.method,
        "email_hint": email_hint(user.email) if two_factor.method == TwoFactorMethod.EMAIL else "",
        "code_sent": sent,
    }


def pending_login(session: SessionBase) -> tuple[LoginState, User] | None:
    state: LoginState | None = session.get(PENDING_LOGIN)
    if not state or time.time() > state.get("expires", 0):
        session.pop(PENDING_LOGIN, None)
        return None
    user = User.objects.filter(pk=state["user"], is_active=True).select_related("two_factor").first()
    if user is None or not hasattr(user, "two_factor"):
        session.pop(PENDING_LOGIN, None)
        return None
    return state, user


def check_login_code(user: User, state: LoginState, code: str) -> bool:
    """The app or email code of the pending login, or one of the user's backup codes."""
    two_factor = user.two_factor
    digits = normalize(code)
    if two_factor.method == TwoFactorMethod.TOTP and len(digits) == TOTP_DIGITS:
        step = match_totp(two_factor.totp_secret, digits, two_factor.totp_last_step)
        if step is not None:
            # Atomic: two requests with the same code cannot both pass.
            return bool(
                TwoFactor.objects.filter(pk=two_factor.pk, totp_last_step__lt=step).update(
                    totp_last_step=step
                )
            )
        return False
    if two_factor.method == TwoFactorMethod.EMAIL and len(digits) == TOTP_DIGITS:
        return match_email_code(state, digits)
    return use_backup_code(user, code)


# --- Setting up ---


def start_setup(session: SessionBase, user: User, method: str) -> SetupResult:
    state: SetupState = {"method": method, "expires": time.time() + PENDING_TTL, "attempts": 0}
    result: SetupResult
    if method == TwoFactorMethod.TOTP:
        state["secret"] = secret = new_totp_secret()
        uri = provisioning_uri(secret, user)
        result = {"method": method, "secret": secret, "uri": uri, "qr_svg": qr_svg(uri)}
    else:
        result = {
            "method": method,
            "email_hint": email_hint(user.email),
            "code_sent": issue_email_code(state, user),
        }
    session[PENDING_SETUP] = state
    return result


def pending_setup(session: SessionBase) -> SetupState | None:
    state: SetupState | None = session.get(PENDING_SETUP)
    if not state or time.time() > state.get("expires", 0):
        session.pop(PENDING_SETUP, None)
        return None
    return state


@transaction.atomic
def finish_setup(user: User, state: SetupState, code: str) -> list[str] | None:
    """Switches the method on when ``code`` fits; returns fresh backup codes."""
    digits = normalize(code)
    if state["method"] == TwoFactorMethod.TOTP:
        step = match_totp(state["secret"], digits)
        if step is None:
            return None
        values: dict[str, str | int] = {
            "method": state["method"],
            "totp_secret": state["secret"],
            "totp_last_step": step,
        }
    else:
        if not match_email_code(state, digits):
            return None
        values = {"method": state["method"], "totp_secret": "", "totp_last_step": 0}
    TwoFactor.objects.update_or_create(user=user, defaults=values)
    return new_backup_codes(user)


@transaction.atomic
def disable(user: User) -> None:
    TwoFactor.objects.filter(user=user).delete()
    BackupCode.objects.filter(user=user).delete()
