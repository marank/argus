"""Block until the database accepts connections (used by the container entrypoint)."""

import time
from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = "Wait until the default database is reachable."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("--timeout", type=int, default=60, help="Seconds before giving up.")

    def handle(self, *args: Any, timeout: int, **options: Any) -> None:
        deadline = time.monotonic() + timeout
        while True:
            try:
                connection.ensure_connection()
            except OperationalError as error:
                if time.monotonic() > deadline:
                    raise CommandError(f"Database not reachable after {timeout}s: {error}") from error
                self.stdout.write("Waiting for database …")
                time.sleep(2)
            else:
                self.stdout.write(self.style.SUCCESS("Database is reachable."))
                return
