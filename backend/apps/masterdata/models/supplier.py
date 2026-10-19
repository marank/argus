from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Supplier(TimeStampedModel):
    name = models.CharField(_("name"), max_length=150, unique=True)
    customer_number = models.CharField(_("customer number"), max_length=50, blank=True)
    contact_person = models.CharField(_("contact person"), max_length=100, blank=True)
    email = models.EmailField(_("email"), blank=True)
    phone = models.CharField(_("phone"), max_length=50, blank=True)
    website = models.URLField(_("website"), blank=True)
    address = models.TextField(_("address"), blank=True)
    notes = models.TextField(_("notes"), blank=True)
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        verbose_name = _("supplier")
        verbose_name_plural = _("suppliers")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
