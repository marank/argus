from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MasterdataConfig(AppConfig):
    name = "apps.masterdata"
    label = "masterdata"
    verbose_name = _("Master data")
