"""``/api/events``: live update signals (``apps.core.live``) as server-sent events.

Served by the ASGI process (uvicorn), where an open stream is a waiting
coroutine rather than a busy worker thread. Each process keeps one PostgreSQL
connection that LISTENs for signals and hands them to the streams of that
process; a stream passes on only what its user may see. The topic "*" asks the
browser to reload everything it shows, e.g. after signals may have been missed.
"""

import asyncio
import json
import logging
from collections import Counter
from typing import Any

import psycopg
from django.conf import settings
from django.core.handlers.asgi import ASGIRequest
from django.db import connections
from django.http import HttpResponse, StreamingHttpResponse

from apps.core.api.security import is_it_staff
from apps.core.live import CHANNEL, visible_to

logger = logging.getLogger(__name__)

# A comment line now and then keeps proxies from closing an idle stream.
PING_SECONDS = 20
# Streams end after a while and the browser reconnects, so sign-outs and changed rights take effect.
STREAM_SECONDS = 30 * 60
RECONNECT_SECONDS = 5
# Open streams per user (one per browser tab); beyond that a tab refreshes as without
# live updates, instead of one user holding any number of connections.
MAX_STREAMS_PER_USER = 20
RELOAD_ALL = {"topic": "*", "id": None}


class Hub:
    """The LISTEN connection of this process and the streams it feeds."""

    def __init__(self):
        self.queues: set[asyncio.Queue[dict[str, Any]]] = set()
        self.streams_per_user: Counter[str] = Counter()
        self.listener: asyncio.Task | None = None
        # Set while LISTEN is active, i.e. signals reach the streams.
        self.listening = asyncio.Event()

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        self.queues.add(queue)
        if self.listener is None or self.listener.done():
            self.listener = asyncio.create_task(self.listen())
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        self.queues.discard(queue)

    def broadcast(self, event: dict) -> None:
        for queue in list(self.queues):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # The stream fell behind: instead of single signals it reloads everything.
                while not queue.empty():
                    queue.get_nowait()
                queue.put_nowait(RELOAD_ALL)

    async def listen(self) -> None:
        params = connections["default"].get_connection_params()
        params.pop("cursor_factory", None)
        params.pop("context", None)
        reconnected = False
        while True:
            try:
                async with await psycopg.AsyncConnection.connect(**params, autocommit=True) as conn:
                    await conn.execute(f"LISTEN {CHANNEL}")
                    self.listening.set()
                    if reconnected:
                        self.broadcast(RELOAD_ALL)  # signals sent in the meantime are lost
                    async for notify in conn.notifies():
                        self.broadcast(json.loads(notify.payload))
            except Exception:  # noqa: BLE001 - keep trying; the streams stay open meanwhile
                logger.exception("Live updates: lost the database connection, retrying")
            self.listening.clear()
            reconnected = True
            await asyncio.sleep(RECONNECT_SECONDS)


hub = Hub()


async def stream(user_id: str, staff: bool):
    queue = hub.subscribe()
    hub.streams_per_user[user_id] += 1
    loop = asyncio.get_running_loop()
    end = loop.time() + STREAM_SECONDS
    try:
        yield "retry: 3000\n\n"
        while (left := end - loop.time()) > 0:
            try:
                event = await asyncio.wait_for(queue.get(), min(PING_SECONDS, left))
            except TimeoutError:
                yield ": ping\n\n"
                continue
            if event is RELOAD_ALL or visible_to(event, user_id, staff):
                yield f"data: {json.dumps({'topic': event['topic'], 'id': event['id']})}\n\n"
        # A planned end: the browser reconnects without reloading everything.
        yield "event: bye\ndata:\n\n"
    finally:
        hub.unsubscribe(queue)
        hub.streams_per_user[user_id] -= 1
        if hub.streams_per_user[user_id] <= 0:
            del hub.streams_per_user[user_id]


async def events(request):
    # Without PostgreSQL there are no signals; under WSGI an endless stream would block a worker.
    # 204 tells the browser's EventSource to stop trying.
    if not settings.LIVE_EVENTS or not isinstance(request, ASGIRequest):
        return HttpResponse(status=204)
    user = await request.auser()
    if not user.is_authenticated:
        return HttpResponse(status=401)
    if hub.streams_per_user[str(user.pk)] >= MAX_STREAMS_PER_USER:
        # EventSource does not retry after this; the page refreshes as without live updates.
        return HttpResponse(status=429)
    response = StreamingHttpResponse(
        stream(str(user.pk), is_it_staff(user)), content_type="text/event-stream"
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
