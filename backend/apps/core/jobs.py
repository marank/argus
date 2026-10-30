"""Deferring background jobs (the tasks themselves live in ``apps.core.tasks``).

With PostgreSQL (``settings.JOB_QUEUE``) a job goes into the Procrastinate queue
within the current transaction: it exists only once the change that caused it is
committed, and ``manage.py procrastinate worker`` runs it, retrying failures. On
SQLite (development, tests) there is no queue: the job runs in-process right after
the commit, and a failure is only logged.
"""

from typing import Any

from django.conf import settings
from django.db import transaction
from procrastinate.exceptions import AlreadyEnqueued
from procrastinate.tasks import Task


def defer[R, **A](task: Task[..., R, A], *, queueing_lock: str | None = None, **kwargs: Any) -> None:
    """Run ``task(**kwargs)`` in the background.

    With ``queueing_lock`` the job is skipped while one with the same lock still
    waits in the queue (e.g. for a retry).
    """
    if settings.JOB_QUEUE:
        try:
            # A savepoint: the rejected insert must not abort the caller's transaction.
            with transaction.atomic():
                task.configure(queueing_lock=queueing_lock).defer(**kwargs)
        except AlreadyEnqueued:
            pass
    else:
        transaction.on_commit(lambda: task(**kwargs), robust=True)
