"""Time-based email notifications on demand.

With PostgreSQL the job worker runs them every hour by itself (``apps.core.tasks``);
this command is for SQLite setups and manual catch-ups.
"""

from typing import Any

from django.core.management.base import BaseCommand

from apps.core.services.reminders import send_due_reminders


class Command(BaseCommand):
    help = "Send due return reminders, overdue notices and license expiry warnings."

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(f"Checked {send_due_reminders()} reminders.")
