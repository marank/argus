import asyncio
import json

import psycopg
import pytest
from asgiref.sync import sync_to_async
from django.db import connection, connections
from django.test import AsyncClient

from apps.accounts.models import User
from apps.core import live_stream
from apps.core.live import CHANNEL
from apps.inventory.models import Asset, AssetIssue
from apps.inventory.services.issues import report_issue

postgres_only = pytest.mark.skipif(
    connection.vendor != "postgresql", reason="live updates need PostgreSQL's LISTEN/NOTIFY"
)


def report(user: User) -> AssetIssue:
    return report_issue(Asset.objects.first(), user, AssetIssue.Kind.DEFECT, "Display flickers")


def test_the_stream_is_unavailable_outside_the_asgi_process(employee_client):
    # Under WSGI (gunicorn, runserver) an endless stream would block a worker.
    assert employee_client.get("/api/events").status_code == 204


@postgres_only
@pytest.mark.django_db(transaction=True)
def test_a_change_is_notified_once_committed(demo):
    employee = User.objects.get(username="employee")
    params = connection.get_connection_params()
    params.pop("cursor_factory", None)
    params.pop("context", None)
    with psycopg.connect(**params, autocommit=True) as listener:
        listener.execute(f"LISTEN {CHANNEL}")
        issue = report(employee)
        payloads = [json.loads(n.payload) for n in listener.notifies(timeout=5, stop_after=1)]
    assert {"topic": "issue", "id": str(issue.pk), "users": [str(employee.pk)], "staff": True} in payloads


@postgres_only
@pytest.mark.django_db(transaction=True)
def test_the_stream_passes_signals_only_to_whom_they_concern(demo, monkeypatch):
    employee = User.objects.get(username="employee")
    it = User.objects.get(username="it")
    stranger = User.objects.create_user("stranger", password="unused")
    # A hub of its own: the module's one may belong to another test's event loop.
    hub = live_stream.Hub()
    monkeypatch.setattr(live_stream, "hub", hub)

    async def open_stream(user):
        client = AsyncClient()
        await client.aforce_login(user)
        response = await client.get("/api/events")
        assert response.status_code == 200
        assert response["Content-Type"] == "text/event-stream"
        stream = aiter(response.streaming_content)
        assert await anext(stream) == b"retry: 3000\n\n"
        return stream

    async def next_event(stream, timeout=5):
        chunk = await asyncio.wait_for(anext(stream), timeout)
        assert chunk.startswith(b"data: ")
        return json.loads(chunk[len(b"data: ") :])

    async def scenario():
        assert (await AsyncClient().get("/api/events")).status_code == 401
        streams = {user.username: await open_stream(user) for user in (it, employee, stranger)}
        await asyncio.wait_for(hub.listening.wait(), 5)

        issue = await sync_to_async(report)(employee)
        expected = {"topic": "issue", "id": str(issue.pk)}
        assert await next_event(streams["it"]) == expected
        assert await next_event(streams["employee"]) == expected
        with pytest.raises(TimeoutError):
            await next_event(streams["stranger"], timeout=1)

        hub.listener.cancel()
        for stream in streams.values():
            await stream.aclose()
        await sync_to_async(connections.close_all)()

    asyncio.run(scenario())
