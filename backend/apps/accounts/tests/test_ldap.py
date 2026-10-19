import os

import pytest
from django.contrib.auth import authenticate
from django.test import Client
from ldap3 import MOCK_SYNC, Connection, Server
from ldap3.core.exceptions import LDAPBindError

from apps.accounts.models import LdapSettings, User
from apps.accounts.services import ldap

SERVICE_DN = "CN=svc-argus,OU=Service,DC=example,DC=com"
ANNA_DN = "CN=Anna Berger,OU=Staff,DC=example,DC=com"

DIRECTORY = {
    SERVICE_DN: {"objectClass": ["user"], "sAMAccountName": "svc-argus", "userPassword": "svc-secret"},
    ANNA_DN: {
        "objectClass": ["user"],
        "sAMAccountName": "ABerger",
        "givenName": "Anna",
        "sn": "Berger",
        "employeeID": "4711",
        "personalNr": "P-0815",
        "mail": "anna.berger@example.com",
        "userPassword": "anna-secret",
    },
}


@pytest.fixture
def directory(monkeypatch):
    """Replace the network connection with an in-memory ldap3 mock directory."""

    def fake_connect(config, user, password):
        connection = Connection(Server("mock"), user=user, password=password, client_strategy=MOCK_SYNC)
        for dn, attributes in DIRECTORY.items():
            connection.strategy.add_entry(dn, attributes)
        if not connection.bind():
            raise LDAPBindError("invalidCredentials")
        return connection

    monkeypatch.setattr(ldap, "_connect", fake_connect)
    for name in list(os.environ):
        if name.startswith(ldap.ENV_PREFIX):
            monkeypatch.delenv(name)


@pytest.fixture
def configured(db, directory):
    settings = LdapSettings.load()
    settings.enabled = True
    settings.server_uri = "ldap://dc.example.com"
    settings.bind_dn = SERVICE_DN
    settings.bind_password = "svc-secret"
    settings.user_search_base = "OU=Staff,DC=example,DC=com"
    settings.save()
    return settings


def test_login_creates_user_from_mapped_attributes(configured):
    user = authenticate(username="aberger", password="anna-secret")
    assert user is not None
    assert user.username == "aberger"
    assert (user.first_name, user.last_name, user.employee_number) == ("Anna", "Berger", "4711")
    assert user.email == "anna.berger@example.com"
    assert user.ldap_dn == ANNA_DN
    assert not user.has_usable_password()


def test_wrong_or_empty_password_is_rejected(configured):
    assert authenticate(username="aberger", password="wrong") is None
    assert authenticate(username="aberger", password="") is None
    assert not User.objects.filter(username="aberger").exists()


def test_filter_injection_is_escaped(configured):
    assert authenticate(username="*", password="anna-secret") is None


def test_disabled_settings_do_not_authenticate(configured):
    configured.enabled = False
    configured.save()
    assert authenticate(username="aberger", password="anna-secret") is None


def test_attribute_mapping_is_configurable_in_app(configured):
    configured.attr_employee_number = "personalNr"
    configured.attr_first_name = "sn"
    configured.save()
    user = authenticate(username="aberger", password="anna-secret")
    assert (user.first_name, user.employee_number) == ("Berger", "P-0815")


def test_environment_overrides_in_app_value(configured, monkeypatch):
    monkeypatch.setenv("LDAP_ATTR_EMPLOYEE_NUMBER", "personalNr")
    monkeypatch.setenv("LDAP_ATTR_PHONE", "")  # empty = unset
    config = ldap.load_config()
    assert config.attr_employee_number == "personalNr"
    assert config.locked == {"attr_employee_number"}
    assert authenticate(username="aberger", password="anna-secret").employee_number == "P-0815"


def test_existing_user_is_linked_and_updated(configured):
    existing = User.objects.create_user("ABERGER", password="local", first_name="Old")
    user = authenticate(username="aberger", password="anna-secret")
    assert user.pk == existing.pk
    assert user.first_name == "Anna"
    assert user.ldap_dn == ANNA_DN


def test_no_user_creation_when_disabled(configured):
    configured.create_users = False
    configured.save()
    assert authenticate(username="aberger", password="anna-secret") is None


def test_local_superuser_is_not_taken_over(configured):
    User.objects.create_superuser("aberger", password="local-admin")
    assert authenticate(username="aberger", password="anna-secret") is None
    assert authenticate(username="aberger", password="local-admin") is not None


def test_settings_api_is_superuser_only_and_hides_password(configured, it_client, monkeypatch):
    assert it_client.get("/api/settings/ldap").status_code == 403

    admin = Client()
    admin.force_login(User.objects.get(username="admin"))
    monkeypatch.setenv("LDAP_SERVER_URI", "ldaps://env.example.com")
    data = admin.get("/api/settings/ldap").json()
    assert data["server_uri"] == "ldaps://env.example.com"
    assert data["locked"] == ["server_uri"]
    assert data["bind_password_set"] is True
    assert "bind_password" not in data

    payload = {**data, "server_uri": "ldap://ignored", "attr_employee_number": "personalNr"}
    for key in ("locked", "env_names", "bind_password_set"):
        payload.pop(key)
    response = admin.put("/api/settings/ldap", payload, content_type="application/json")
    assert response.status_code == 200
    configured.refresh_from_db()
    assert configured.server_uri == "ldap://dc.example.com"  # locked field untouched
    assert configured.attr_employee_number == "personalNr"
    assert configured.bind_password == "svc-secret"  # None keeps the password

    response = admin.post(
        "/api/settings/ldap/test", {**payload, "username": "aberger"}, content_type="application/json"
    )
    assert response.status_code == 200, response.json()
    assert response.json()["user"]["employee_number"] == "P-0815"

    response = admin.post(
        "/api/settings/ldap/test",
        {**payload, "bind_password": "wrong"},
        content_type="application/json",
    )
    assert response.status_code == 400
