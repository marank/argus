from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ProcurementConfig(AppConfig):
    name = "apps.procurement"
    label = "procurement"
    verbose_name = _("Procurement")

    def ready(self):
        from . import live

        live.connect()
