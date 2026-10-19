from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Department(TimeStampedModel):
    name = models.CharField(_("name"), max_length=100, unique=True)
    code = models.CharField(_("code"), max_length=20, blank=True)
    cost_center = models.CharField(_("cost center"), max_length=30, blank=True)

    class Meta:
        verbose_name = _("department")
        verbose_name_plural = _("departments")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
