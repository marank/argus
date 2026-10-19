import pytest
from django.core.management import call_command
from django.test import Client


@pytest.fixture
def demo(db):
    call_command("seed_demo", verbosity=0)


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
