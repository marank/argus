from typing import Any

from django.contrib.auth.backends import ModelBackend
from django.http import HttpRequest

from apps.accounts.models import User
from apps.accounts.services import ldap


class LdapBackend(ModelBackend):
    """Signs in employees against LDAP / Active Directory (see ``apps.accounts.services.ldap``).

    Listed after ``ModelBackend``: local accounts (administrator, pickup terminal) keep
    working when the directory is down or not configured.
    """

    def authenticate(
        self,
        request: HttpRequest | None,
        username: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> User | None:
        user = ldap.authenticate(username or "", password or "")
        return user if user is not None and self.user_can_authenticate(user) else None
