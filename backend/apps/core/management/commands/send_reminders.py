"""Time-based email notifications; run regularly (the Docker image does so every hour).

Each reminder goes out once per recipient (see ``NotificationLog``), so running
the command more often or catching up after a pause is safe.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.features import is_enabled
from apps.core.models import SiteSettings
from apps.inventory.models import License
from apps.inventory.services import notifications as inventory_notifications
from apps.reservations.models import Reservation
from apps.reservations.services import notifications as reservation_notifications


class Command(BaseCommand):
    help = "Send due return reminders, overdue notices and license expiry warnings."

    def handle(self, *args, **options):
        settings = SiteSettings.load()
        today = timezone.localdate()
        sent = 0

        lent = Reservation.objects.filter(
            duration=Reservation.Duration.TEMPORARY, status=Reservation.Status.HANDED_OUT
        ).select_related("requester")
        due_soon = lent.filter(end_date__range=(today, today + timedelta(days=settings.return_reminder_days)))
        for reservation in due_soon:
            reservation_notifications.return_reminder(reservation)
            sent += 1
        for reservation in lent.filter(end_date__lt=today):
            reservation_notifications.return_overdue(reservation)
            sent += 1

        if is_enabled("licenses"):
            ending = License.objects.select_related("model__manufacturer").filter(
                valid_until__range=(today, today + timedelta(days=settings.license_warning_days))
            )
            for license in ending:
                inventory_notifications.license_expiring(license)
                sent += 1

        self.stdout.write(f"Checked {sent} reminders.")
