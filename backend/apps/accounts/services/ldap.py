"""LDAP / Active Directory login.

The configuration is the ``LdapSettings`` row, overridden field by field by
environment variables ``LDAP_<FIELD>`` (``LDAP_SERVER_URI``, ``LDAP_BIND_PASSWORD``,
``LDAP_ATTR_FIRST_NAME``, …). Empty variables count as unset, so compose files may
pass ``LDAP_X=${LDAP_X:-}`` without locking the in-app value.

Login: search the user with the service account (or anonymously), bind as the found
DN with the entered password, then create or update the Argus user from the mapped
attributes. The directory wins: first/last name, employee number etc. are overwritten
at every login, and so is the membership in teams linked to an LDAP group.
"""

import logging
import os
import ssl
from dataclasses import dataclass, fields
from typing import Any

from django.db import transaction
from django.utils.translation import gettext as _
from ldap3 import (
    AUTO_BIND_NO_TLS,
    AUTO_BIND_TLS_BEFORE_BIND,
    BASE,
    NONE,
    SUBTREE,
    Connection,
    Server,
    Tls,
)
from ldap3.core.exceptions import LDAPBindError, LDAPException
from ldap3.utils.conv import escape_filter_chars

from apps.accounts.models import LdapSettings, Team, User

logger = logging.getLogger(__name__)

ENV_PREFIX = "LDAP_"

# Argus user field -> config field naming the LDAP attribute.
ATTRIBUTE_MAP = {
    "first_name": "attr_first_name",
    "last_name": "attr_last_name",
    "employee_number": "attr_employee_number",
    "email": "attr_email",
    "job_title": "attr_job_title",
    "phone": "attr_phone",
}


class LdapError(Exception):
    """Configuration or connection problem, with a message for administrators."""


@dataclass(frozen=True)
class LdapConfig:
    enabled: bool
    server_uri: str
    start_tls: bool
    verify_cert: bool
    ca_cert_file: str
    timeout: int
    bind_dn: str
    bind_password: str
    user_search_base: str
    user_filter: str
    attr_username: str
    attr_first_name: str
    attr_last_name: str
    attr_employee_number: str
    attr_email: str
    attr_job_title: str
    attr_phone: str
    create_users: bool
    # Fields set by environment variables (read-only in the app).
    locked: frozenset[str] = frozenset()

    @property
    def is_usable(self) -> bool:
        return self.enabled and bool(self.server_uri and self.user_search_base and self.user_filter)


CONFIG_FIELDS = [f.name for f in fields(LdapConfig) if f.name != "locked"]


def env_name(field: str) -> str:
    return ENV_PREFIX + field.upper()


def _parse(field: str, raw: str) -> Any:
    kind = LdapConfig.__dataclass_fields__[field].type
    if kind is bool:
        return raw.strip().lower() in {"1", "true", "yes", "on"}
    if kind is int:
        try:
            return int(raw)
        except ValueError as exc:
            raise LdapError(_("%(name)s must be a number.") % {"name": env_name(field)}) from exc
    return raw.strip()


def env_overrides() -> dict[str, Any]:
    """Config values set through (non-empty) environment variables."""
    values = {}
    for field in CONFIG_FIELDS:
        raw = os.environ.get(env_name(field), "")
        if raw.strip():
            values[field] = _parse(field, raw)
    return values


def load_config(stored: LdapSettings | None = None, **changes: Any) -> LdapConfig:
    """Effective configuration: stored row, then ``changes`` (unsaved form), then environment."""
    stored = stored or LdapSettings.load()
    values = {field: getattr(stored, field) for field in CONFIG_FIELDS}
    values.update(changes)
    overrides = env_overrides()
    values.update(overrides)
    return LdapConfig(**values, locked=frozenset(overrides))


# --- Directory access ---------------------------------------------------------------


def _servers(config: LdapConfig) -> list[Server]:
    tls = Tls(
        validate=ssl.CERT_REQUIRED if config.verify_cert else ssl.CERT_NONE,
        ca_certs_file=config.ca_cert_file or None,
    )
    servers = [
        Server(uri.strip(), tls=tls, connect_timeout=config.timeout, get_info=NONE)
        for uri in config.server_uri.split(",")
        if uri.strip()
    ]
    if not servers:
        raise LdapError(_("No LDAP server configured."))
    return servers


def _connect(config: LdapConfig, user: str | None, password: str | None) -> Connection:
    """Open a bound connection to the first reachable server.

    Raises ``LDAPBindError`` for wrong credentials and the last connection error when
    no server answers. (ldap3's ServerPool would sleep between rounds; a login must not.)
    """
    error: LDAPException | None = None
    for server in _servers(config):
        try:
            return Connection(
                server,
                user=user or None,
                password=password or None,
                auto_bind=AUTO_BIND_TLS_BEFORE_BIND if config.start_tls else AUTO_BIND_NO_TLS,
                receive_timeout=config.timeout,
                read_only=True,
                raise_exceptions=False,
            )
        except LDAPBindError:
            raise
        except LDAPException as exc:
            logger.warning("LDAP server %s not reachable: %s", server, exc)
            error = exc
    raise error


def _service_connection(config: LdapConfig) -> Connection:
    try:
        return _connect(config, config.bind_dn, config.bind_password)
    except LDAPBindError as exc:
        raise LdapError(_("The service account could not sign in: %(error)s") % {"error": exc}) from exc
    except LDAPException as exc:
        raise LdapError(_("LDAP server not reachable: %(error)s") % {"error": exc}) from exc


def _first_value(attributes: dict, name: str) -> str:
    if not name:
        return ""
    value = attributes.get(name)
    if isinstance(value, list | tuple):
        value = value[0] if value else ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    return str(value or "").strip()


@dataclass(frozen=True)
class DirectoryUser:
    dn: str
    username: str
    values: dict[str, str]  # Argus user field -> value


def find_user(config: LdapConfig, connection: Connection, username: str) -> DirectoryUser | None:
    search_filter = config.user_filter.replace("{username}", escape_filter_chars(username))
    attributes = [config.attr_username] + [
        getattr(config, attr) for attr in ATTRIBUTE_MAP.values() if getattr(config, attr)
    ]
    ok = connection.search(
        config.user_search_base, search_filter, SUBTREE, attributes=attributes, size_limit=2
    )
    if not ok and connection.result.get("description") not in ("success", "noSuchObject"):
        raise LdapError(
            _("LDAP search failed: %(error)s")
            % {"error": connection.result.get("message") or connection.result.get("description")}
        )
    entries = [e for e in connection.response or [] if e.get("type") == "searchResEntry"]
    if len(entries) != 1:
        if len(entries) > 1:
            logger.warning("LDAP filter matches several entries for %r; refusing login", username)
        return None
    entry = entries[0]
    attrs = entry.get("attributes", {})
    return DirectoryUser(
        dn=entry["dn"],
        username=(_first_value(attrs, config.attr_username) or username).lower(),
        values={
            field: _first_value(attrs, getattr(config, attr))
            for field, attr in ATTRIBUTE_MAP.items()
            if getattr(config, attr)
        },
    )


def _check_password(config: LdapConfig, dn: str, password: str) -> bool:
    try:
        _connect(config, dn, password).unbind()
    except LDAPBindError:
        return False
    return True


# --- Argus users --------------------------------------------------------------------


def _truncate(field: str, value: str) -> str:
    return value[: User._meta.get_field(field).max_length]


@transaction.atomic
def sync_user(config: LdapConfig, entry: DirectoryUser) -> User | None:
    """Create or update the Argus user for a directory entry (``None`` = not allowed)."""
    user = (
        User.objects.select_for_update().filter(ldap_dn__iexact=entry.dn).first()
        or User.objects.select_for_update().filter(username__iexact=entry.username).first()
    )
    if user is None:
        if not config.create_users:
            return None
        user = User(username=_truncate("username", entry.username))
        user.set_unusable_password()
    elif not user.ldap_dn and user.is_superuser:
        # Local superusers stay local: a directory account of the same name must not take them over.
        logger.warning("LDAP login for local superuser %r refused", user.username)
        return None

    user.ldap_dn = _truncate("ldap_dn", entry.dn)
    for field, value in entry.values.items():
        setattr(user, field, _truncate(field, value))
    user.save()
    return user


def _is_group_member(connection: Connection, group_dn: str, member_dn: str) -> bool | None:
    """Direct membership of ``member_dn`` in the group (AD ``member`` or ``uniqueMember``).

    ``None`` when the group cannot be read, so the membership is left as it is.
    """
    dn = escape_filter_chars(member_dn)
    connection.search(group_dn, f"(|(member={dn})(uniqueMember={dn}))", BASE, attributes=[])
    if connection.result.get("description") != "success":
        logger.warning("LDAP group %s not readable: %s", group_dn, connection.result.get("description"))
        return None
    return any(e.get("type") == "searchResEntry" for e in connection.response or [])


def sync_teams(config: LdapConfig, user: User) -> None:
    """Add the user to or remove them from the teams linked to an LDAP group."""
    teams = list(Team.objects.exclude(ldap_group_dn=""))
    if not teams or not user.ldap_dn:
        return
    connection = _service_connection(config)
    try:
        for team in teams:
            member = _is_group_member(connection, team.ldap_group_dn, user.ldap_dn)
            if member is True:
                team.members.add(user)
            elif member is False:
                team.members.remove(user)
    finally:
        connection.unbind()


def authenticate(username: str, password: str) -> User | None:
    """Check credentials against the directory; ``None`` on any failure (logged)."""
    # An empty password would be an anonymous ("unauthenticated") bind that always succeeds.
    if not username or not password:
        return None
    try:
        config = load_config()
        if not config.is_usable:
            return None
        connection = _service_connection(config)
        try:
            entry = find_user(config, connection, username)
        finally:
            connection.unbind()
        if entry is None or not _check_password(config, entry.dn, password):
            return None
        user = sync_user(config, entry)
    except (LdapError, LDAPException) as exc:
        logger.error("LDAP login failed: %s", exc)
        return None
    if user is not None:
        # Team membership is a convenience; a directory hiccup must not block the login.
        try:
            sync_teams(config, user)
        except (LdapError, LDAPException) as exc:
            logger.error("LDAP team sync for %s failed: %s", user.username, exc)
    return user


def test_connection(config: LdapConfig, username: str = "") -> dict:
    """Bind with the service account and optionally look up a user (no password check)."""
    if not config.server_uri:
        raise LdapError(_("No LDAP server configured."))
    if not config.user_search_base:
        raise LdapError(_("No user search base configured."))
    connection = _service_connection(config)
    try:
        entry = find_user(config, connection, username) if username else None
    finally:
        connection.unbind()
    if username and entry is None:
        message = _("Connected, but no unique entry found for “%(username)s”.")
        raise LdapError(message % {"username": username})
    return {
        "server": str(connection.server),
        "user": None if entry is None else {"dn": entry.dn, "username": entry.username, **entry.values},
    }
