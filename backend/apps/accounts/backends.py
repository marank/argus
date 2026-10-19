from django.contrib.auth.backends import ModelBackend

from apps.accounts.services import ldap


class LdapBackend(ModelBackend):
    """Signs in employees against LDAP / Active Directory (see ``apps.accounts.services.ldap``).

    Listed after ``ModelBackend``: local accounts (administrator, pickup terminal) keep
    working when the directory is down or not configured.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        user = ldap.authenticate(username or "", password or "")
        return user if user is not None and self.user_can_authenticate(user) else None
