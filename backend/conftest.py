import pytest
from django.test import Client

from apps.core.management.commands.seed_demo import Command


@pytest.fixture(autouse=True)
def in_memory_mail(settings):
    """Notifications never reach a real SMTP server in tests (see django.core.mail.outbox)."""
    settings.ARGUS_EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


@pytest.fixture
def demo(db):
    # Only the core part of the demo data: keeps the tests fast and their expectations stable.
    Command().seed_base()


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
