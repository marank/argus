from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ReservationsConfig(AppConfig):
    name = "apps.reservations"
    label = "reservations"
    verbose_name = _("Reservations")

    def ready(self):
        from . import live

        live.connect()
