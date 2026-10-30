"""The user's own two-factor sign-in: switch it on, change the method, new backup codes, switch off."""

from typing import TypedDict

from django.contrib.auth import authenticate
from django.utils.translation import gettext as _
from ninja import Router, Status
from ninja.errors import HttpError

from apps.accounts.models import TwoFactor, User
from apps.accounts.schemas import (
    BackupCodesOut,
    CodeIn,
    PasswordIn,
    TwoFactorSetupIn,
    TwoFactorSetupOut,
    TwoFactorStatusOut,
)
from apps.accounts.services import throttle, two_factor
from apps.core.api.security import AuthedRequest, employee_auth

router = Router(tags=["auth"], auth=employee_auth)


def confirm_password(request: AuthedRequest, password: str) -> None:
    """Changes to the sign-in need the password, not just an open session."""
    user = request.user
    key = throttle.password_key(user.username)
    if not throttle.attempt(key, throttle.PASSWORD_LIMIT):
        raise HttpError(429, _("Too many failed attempts. Please try again in 15 minutes."))
    checked = authenticate(request, username=user.username, password=password)
    if checked is None or checked.pk != user.pk:
        # Not 401: that would end the session in the frontend.
        raise HttpError(403, _("The password is not correct."))
    throttle.clear(key)


class TwoFactorStatus(TypedDict):
    method: str | None
    backup_codes_left: int
    email_available: bool
    email_hint: str


def status(user: User) -> TwoFactorStatus:
    return {
        "method": two_factor.method_of(user),
        "backup_codes_left": two_factor.backup_codes_left(user),
        "email_available": two_factor.email_available(user),
        "email_hint": two_factor.email_hint(user.email) if user.email else "",
    }


@router.get("", response=TwoFactorStatusOut)
def get_status(request: AuthedRequest) -> TwoFactorStatus:
    return status(request.user)


@router.post("/setup", response=TwoFactorSetupOut)
def start_setup(request: AuthedRequest, payload: TwoFactorSetupIn) -> two_factor.SetupResult:
    """First step of switching a method on: the QR code, or a code sent by email."""
    confirm_password(request, payload.password)
    if payload.method == TwoFactor.Method.EMAIL.value and not two_factor.email_available(request.user):
        raise HttpError(
            409, _("Codes by email require an email address on file and configured email delivery.")
        )
    return two_factor.start_setup(request.session, request.user, payload.method)


@router.post("/setup/resend", response=TwoFactorSetupOut)
def resend_setup_code(request: AuthedRequest) -> two_factor.SetupResult:
    state = two_factor.pending_setup(request.session)
    if state is None or state["method"] != TwoFactor.Method.EMAIL:
        raise HttpError(409, _("The setup has expired. Please start again."))
    if not two_factor.can_resend(state):
        raise HttpError(429, _("Please wait a moment before requesting another code."))
    sent = two_factor.issue_email_code(state, request.user)
    request.session[two_factor.PENDING_SETUP] = state
    return {"method": "email", "email_hint": two_factor.email_hint(request.user.email), "code_sent": sent}


@router.post("/setup/confirm", response=BackupCodesOut)
def confirm_setup(request: AuthedRequest, payload: CodeIn) -> dict[str, list[str]]:
    """Second step: the first code proves the app or address works; returns new backup codes."""
    state = two_factor.pending_setup(request.session)
    if state is None:
        raise HttpError(409, _("The setup has expired. Please start again."))
    if not throttle.attempt(throttle.code_key(request.user), throttle.CODE_LIMIT):
        request.session.pop(two_factor.PENDING_SETUP, None)
        raise HttpError(429, _("Too many wrong codes. Please try again in 15 minutes."))
    codes = two_factor.finish_setup(request.user, state, payload.code)
    if codes is None:
        state["attempts"] += 1
        if state["attempts"] >= two_factor.MAX_ATTEMPTS:
            request.session.pop(two_factor.PENDING_SETUP, None)
            raise HttpError(409, _("Too many wrong codes. Please start again."))
        request.session[two_factor.PENDING_SETUP] = state
        raise HttpError(400, _("The code is not correct or has expired."))
    request.session.pop(two_factor.PENDING_SETUP, None)
    throttle.clear(throttle.code_key(request.user))
    return {"backup_codes": codes}


@router.post("/backup-codes", response=BackupCodesOut)
def renew_backup_codes(request: AuthedRequest, payload: PasswordIn) -> dict[str, list[str]]:
    """New backup codes; the old ones stop working."""
    confirm_password(request, payload.password)
    if two_factor.method_of(request.user) is None:
        raise HttpError(409, _("Enable two-factor authentication first."))
    return {"backup_codes": two_factor.new_backup_codes(request.user)}


@router.post("/disable", response={204: None})
def disable(request: AuthedRequest, payload: PasswordIn) -> Status[None]:
    confirm_password(request, payload.password)
    two_factor.disable(request.user)
    return Status(204, None)
