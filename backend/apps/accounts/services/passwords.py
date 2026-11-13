"""Passwords of local accounts: changed by the user, or set by an administrator.

Directory (LDAP) accounts are left alone: their password lives in the directory, and a
local one would be checked first and work alongside it.
"""

import logging

from django.contrib.auth.password_validation import validate_password

from apps.accounts.models import User
from apps.accounts.services import throttle

logger = logging.getLogger(__name__)


def may_change_own(user: User) -> bool:
    """Whether the user can change their own password in the profile."""
    return not user.is_ldap_user and user.can_change_password and user.has_usable_password()


def set_password(user: User, password: str) -> None:
    """Checks the password against the password rules and stores it.

    Raises ``ValidationError`` with the broken rules. Other sessions of the user end,
    since the session hash changes with the password; lockouts of the account are lifted.
    """
    validate_password(password, user)
    user.set_password(password)
    user.save(update_fields=["password"])
    throttle.clear(throttle.password_key(user.username))
    throttle.clear(throttle.code_key(user))
