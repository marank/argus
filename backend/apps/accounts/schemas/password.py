from apps.core.schemas.base import Schema


class PasswordChangeIn(Schema):
    current_password: str
    new_password: str


class PasswordSetIn(Schema):
    password: str
