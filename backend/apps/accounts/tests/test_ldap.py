import os

import pytest
from django.contrib.auth import authenticate
from django.test import Client
from ldap3 import MOCK_SYNC, Connection, Server
from ldap3.core.exceptions import LDAPBindError

from apps.accounts.models import LdapSettings, Team, User
from apps.accounts.services import ldap

SERVICE_DN = "CN=svc-argus,OU=Service,DC=example,DC=com"
ANNA_DN = "CN=Anna Berger,OU=Staff,DC=example,DC=com"
BERND_DN = "CN=Bernd Meier,OU=Staff,DC=example,DC=com"
NONAME_DN = "CN=Meeting Room,OU=Staff,DC=example,DC=com"
LEDGERLINE_DN = "CN=IT-Ledgerline,OU=Groups,DC=example,DC=com"
SUPPORT_DN = "CN=IT-Support,OU=Groups,DC=example,DC=com"

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
    BERND_DN: {
        "objectClass": ["user"],
        "sAMAccountName": "BMeier",
        "givenName": "Bernd",
        "sn": "Meier",
        "userPassword": "bernd-secret",
    },
    NONAME_DN: {"objectClass": ["user"], "givenName": "Meeting"},
    LEDGERLINE_DN: {"objectClass": ["group"], "member": [ANNA_DN]},
    SUPPORT_DN: {"objectClass": ["group"], "member": [SERVICE_DN]},
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
    assert user is not None
    assert (user.first_name, user.employee_number) == ("Berger", "P-0815")


def test_environment_overrides_in_app_value(configured, monkeypatch):
    monkeypatch.setenv("LDAP_ATTR_EMPLOYEE_NUMBER", "personalNr")
    monkeypatch.setenv("LDAP_ATTR_PHONE", "")  # empty = unset
    config = ldap.load_config()
    assert config.attr_employee_number == "personalNr"
    assert config.locked == {"attr_employee_number"}
    user = authenticate(username="aberger", password="anna-secret")
    assert user is not None
    assert user.employee_number == "P-0815"


def test_existing_user_is_linked_and_updated(configured):
    existing = User.objects.create_user("ABERGER", password="local", first_name="Old")
    user = authenticate(username="aberger", password="anna-secret")
    assert user is not None
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


def api_login(username: str, password: str):
    return Client().post(
        "/api/auth/login", {"username": username, "password": password}, content_type="application/json"
    )


def test_local_accounts_log_in_while_ldap_is_on(configured):
    User.objects.create_user("local-admin", password="local-secret", is_superuser=True, is_staff=True)
    User.objects.create_user("local-user", password="local-secret")
    assert api_login("local-admin", "local-secret").status_code == 200
    assert api_login("local-user", "local-secret").status_code == 200
    # Directory accounts still work next to them.
    assert api_login("ABerger", "anna-secret").status_code == 200


def test_local_login_works_when_the_directory_is_down(configured, monkeypatch):
    from ldap3.core.exceptions import LDAPSocketOpenError

    def unreachable(config, user, password):
        raise LDAPSocketOpenError("unable to open socket")

    monkeypatch.setattr(ldap, "_connect", unreachable)
    User.objects.create_user("local-user", password="local-secret")
    assert api_login("local-user", "local-secret").status_code == 200
    assert api_login("ABerger", "anna-secret").status_code == 401


def test_local_password_of_a_linked_account_keeps_working(configured):
    # A local account that also exists in the directory: both passwords work.
    User.objects.create_user("ABerger", password="local-secret")
    assert api_login("ABerger", "anna-secret").status_code == 200
    assert User.objects.get(username="ABerger").ldap_dn == ANNA_DN
    assert api_login("ABerger", "local-secret").status_code == 200


def test_team_membership_follows_ldap_groups(configured):
    ledgerline = Team.objects.create(name="Ledgerline", ldap_group_dn=LEDGERLINE_DN)
    support = Team.objects.create(name="IT-Support", ldap_group_dn=SUPPORT_DN)
    missing = Team.objects.create(name="Old", ldap_group_dn="CN=Gone,OU=Groups,DC=example,DC=com")
    manual = Team.objects.create(name="Manual")

    user = User.objects.create_user("aberger")
    support.members.add(user)  # no longer in the group: removed at login
    missing.members.add(user)  # group unreadable: membership kept
    manual.members.add(user)  # no LDAP group: left alone

    logged_in = authenticate(username="aberger", password="anna-secret")
    assert logged_in is not None
    assert set(logged_in.teams.values_list("name", flat=True)) == {"Ledgerline", "Old", "Manual"}
    assert not ledgerline.members.exclude(pk=logged_in.pk).exists()


def test_site_settings_tell_whether_ldap_is_on(configured, it_client):
    assert it_client.get("/api/settings/site").json()["ldap_enabled"] is True
    configured.enabled = False
    configured.save()
    assert it_client.get("/api/settings/site").json()["ldap_enabled"] is False


def test_changed_server_needs_the_bind_password_again(configured, demo):
    admin = Client()
    admin.force_login(User.objects.get(username="admin"))
    data = admin.get("/api/settings/ldap").json()
    for key in ("locked", "env_names", "bind_password_set"):
        data.pop(key)

    # The stored password must not go to another server, neither in a test nor saved.
    elsewhere = {**data, "server_uri": "ldap://attacker.example.com"}
    for method, path in ((admin.post, "/api/settings/ldap/test"), (admin.put, "/api/settings/ldap")):
        response = method(path, elsewhere, content_type="application/json")
        assert response.status_code == 400, response.content
        assert "bind password" in response.json()["detail"]
    configured.refresh_from_db()
    assert configured.server_uri == "ldap://dc.example.com"

    # With the password typed in, or with the server unchanged, it works as before.
    response = admin.put(
        "/api/settings/ldap", {**elsewhere, "bind_password": "svc-secret"}, content_type="application/json"
    )
    assert response.status_code == 200
    response = admin.put(
        "/api/settings/ldap",
        {**elsewhere, "user_filter": data["user_filter"]},
        content_type="application/json",
    )
    assert response.status_code == 200


def sync(client: Client, step: str, **data):
    return client.post(f"/api/settings/ldap/sync/{step}", data, content_type="application/json")


def test_sync_preview_tells_what_would_change(configured, admin_client):
    User.objects.create_user("bmeier", first_name="Old", last_name="Meier")
    response = sync(admin_client, "preview", filter="(&(objectClass=user)(sAMAccountName={username}))")
    assert response.status_code == 200, response.content
    items = {i["dn"]: i for i in response.json()["items"]}
    assert set(items) == {ANNA_DN, BERND_DN}  # the search base leaves out the service account

    assert items[ANNA_DN]["action"] == "create"
    assert items[ANNA_DN]["changes"]["employee_number"] == {"old": "", "new": "4711"}
    bernd = items[BERND_DN]
    assert bernd["action"] == "update"
    assert set(bernd["changes"]) == {"first_name", "ldap_dn"}
    assert bernd["changes"]["first_name"] == {"old": "Old", "new": "Bernd"}
    # Only a preview.
    assert not User.objects.filter(username="aberger").exists()
    assert User.objects.get(username="bmeier").first_name == "Old"


def test_sync_preview_skips_entries_it_must_not_take_over(configured, admin_client):
    User.objects.create_superuser("aberger", password="local-admin")
    response = sync(admin_client, "preview", filter="objectClass=user")
    items = {i["dn"]: i for i in response.json()["items"]}
    assert (items[ANNA_DN]["action"], items[ANNA_DN]["reason"]) == ("skipped", "superuser")
    assert (items[NONAME_DN]["action"], items[NONAME_DN]["reason"]) == ("skipped", "no_username")


def test_sync_apply_takes_over_the_chosen_entries(configured, admin_client):
    configured.create_users = False  # the explicit sync creates users anyway
    configured.save()
    ledgerline = Team.objects.create(name="Ledgerline", ldap_group_dn=LEDGERLINE_DN)
    User.objects.create_user("bmeier", first_name="Old")
    query = {"filter": "(objectClass=user)", "search_base": ""}

    response = sync(admin_client, "apply", **query, dns=[ANNA_DN.lower(), NONAME_DN])
    assert response.status_code == 200, response.content
    assert response.json() == {"created": 1, "updated": 0, "skipped": 1}
    anna = User.objects.get(username="aberger")
    assert (anna.employee_number, anna.ldap_dn) == ("4711", ANNA_DN)
    assert not anna.has_usable_password()
    assert list(ledgerline.members.all()) == [anna]
    assert User.objects.get(username="bmeier").first_name == "Old"  # not chosen

    # A second run finds nothing left to do for Anna.
    items = sync(admin_client, "preview", **query).json()["items"]
    assert {i["dn"]: i["action"] for i in items}[ANNA_DN] == "unchanged"


def test_sync_rejects_bad_filters_and_non_admins(configured, it_client, admin_client):
    assert sync(it_client, "preview", filter="(objectClass=user)").status_code == 403
    response = sync(admin_client, "preview", filter="(objectClass=user")
    assert response.status_code == 400
    assert "filter" in response.json()["detail"]

    configured.enabled = False
    configured.save()
    assert sync(admin_client, "preview", filter="(objectClass=user)").status_code == 400
