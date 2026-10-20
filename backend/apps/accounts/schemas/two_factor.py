from typing import Literal

from ninja import Schema

Method = Literal["email", "totp"]


class TwoFactorChallengeOut(Schema):
    """Answer of the login when a second step is needed (HTTP 202)."""

    two_factor: Method
    # Email method: where the code went (``m***@example.com``) and whether it went out.
    email_hint: str = ""
    code_sent: bool = False


class CodeIn(Schema):
    code: str


class PasswordIn(Schema):
    password: str


class TwoFactorStatusOut(Schema):
    method: Method | None
    backup_codes_left: int
    # Codes by email can reach the user (address set, mail sending configured).
    email_available: bool
    email_hint: str


class TwoFactorSetupIn(Schema):
    method: Method
    password: str


class TwoFactorSetupOut(Schema):
    method: Method
    # Authenticator app: the secret to type in, the otpauth link and it as QR code (SVG data URI).
    secret: str = ""
    uri: str = ""
    qr_svg: str = ""
    # Email: where the confirmation code went.
    email_hint: str = ""
    code_sent: bool = False


class BackupCodesOut(Schema):
    backup_codes: list[str]
