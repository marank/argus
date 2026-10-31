import pytest
from django.core.management import call_command
from django.test import Client, override_settings

from apps.accounts.models import User
from apps.core.management.commands.seed_demo import Command
from apps.core.models import MailSettings

IN_MEMORY_MAIL = {
    "ARGUS_EMAIL_BACKEND": "django.core.mail.backends.locmem.EmailBackend",
    "JOB_QUEUE": False,
}
FAST_PASSWORD_HASHING = {"PASSWORD_HASHERS": ["django.contrib.auth.hashers.MD5PasswordHasher"]}


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Seeds the core demo data once per test database; every test rolls back on top of it.

    Seeding per test cost ~0.7 s each, most of the suite's run time."""
    with django_db_blocker.unblock(), override_settings(**IN_MEMORY_MAIL, **FAST_PASSWORD_HASHING):
        Command().seed_base()


@pytest.fixture(autouse=True)
def in_memory_mail(settings):
    """Notifications never reach a real SMTP server in tests (see django.core.mail.outbox).

    They also go out right after the commit instead of through the job queue, so
    tests read them from the outbox on PostgreSQL too; the queue itself is
    covered by apps/core/tests/test_jobs.py (with ``job_queue``).
    """
    for name, value in IN_MEMORY_MAIL.items():
        setattr(settings, name, value)


@pytest.fixture(autouse=True)
def fast_password_hashing(settings):
    """Tests create and log in users all the time; the real hasher would take seconds."""
    settings.PASSWORD_HASHERS = FAST_PASSWORD_HASHING["PASSWORD_HASHERS"]


@pytest.fixture
def demo(db):
    # Only the core part of the demo data: keeps the tests fast and their expectations stable.
    # Already there from django_db_setup, unless a transactional test emptied the database.
    if not User.objects.filter(username="admin").exists():
        Command().seed_base()


@pytest.fixture
def empty_db(db):
    """For the tests that seed themselves: the shared demo data is gone until the rollback."""
    call_command("flush", interactive=False, verbosity=0)


@pytest.fixture
def mail_on(demo) -> MailSettings:
    settings = MailSettings.load()
    settings.enabled = True
    settings.host = "smtp.example.com"
    settings.from_email = "argus@example.com"
    settings.app_url = "https://argus.example.com"
    settings.save()
    return settings


@pytest.fixture
def admin_client(demo) -> Client:
    """The demo administrator (replaces pytest-django's fixture of that name)."""
    client = Client()
    client.login(username="admin", password="argus-demo")
    return client


@pytest.fixture
def it_client(demo) -> Client:
    client = Client()
    client.login(username="it", password="argus-demo")
    return client


@pytest.fixture
def employee_client(demo) -> Client:
    client = Client()
    client.login(username="employee", password="argus-demo")
    return client


@pytest.fixture
def terminal_client(demo) -> Client:
    client = Client()
    client.login(username="terminal", password="argus-demo")
    return client
