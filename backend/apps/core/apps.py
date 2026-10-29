from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CoreConfig(AppConfig):
    name = "apps.core"
    label = "core"
    verbose_name = _("Core")

    def ready(self) -> None:
        from . import checks  # noqa: F401 - registers the system checks
