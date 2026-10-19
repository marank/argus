from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import UUIDModel


class DeviceReturn(UUIDModel):
    """Record of devices (and license seats) taken back from a reservation at one time."""

    reservation = models.ForeignKey(
        "reservations.Reservation",
        verbose_name=_("reservation"),
        on_delete=models.CASCADE,
        related_name="returns",
    )
    notes = models.TextField(_("notes"), blank=True)
    returned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("taken back by"),
        on_delete=models.SET_NULL,
        null=True,
        related_name="+",
    )
    returned_at = models.DateTimeField(_("returned at"), auto_now_add=True)

    class Meta:
        verbose_name = _("return")
        verbose_name_plural = _("returns")
        ordering = ["returned_at"]

    def __str__(self) -> str:
        return f"{self.reservation.number} ← {self.returned_at:%Y-%m-%d %H:%M}"
