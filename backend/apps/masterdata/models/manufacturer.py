from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Manufacturer(TimeStampedModel):
    name = models.CharField(_("name"), max_length=100, unique=True)
    website = models.URLField(_("website"), blank=True)
    support_url = models.URLField(_("support URL"), blank=True)
    support_phone = models.CharField(_("support phone"), max_length=50, blank=True)
    notes = models.TextField(_("notes"), blank=True)
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        verbose_name = _("manufacturer")
        verbose_name_plural = _("manufacturers")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
