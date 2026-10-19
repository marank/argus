from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import UUIDModel


class ReservationAllocation(UUIDModel):
    """A concrete device (or consumable quantity) set aside for a reservation item."""

    item = models.ForeignKey(
        "reservations.ReservationItem",
        verbose_name=_("reservation item"),
        on_delete=models.CASCADE,
        related_name="allocations",
    )
    asset = models.ForeignKey(
        "inventory.Asset",
        verbose_name=_("asset"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reservation_allocations",
    )
    consumable = models.ForeignKey(
        "inventory.Consumable",
        verbose_name=_("consumable"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reservation_allocations",
    )
    quantity = models.PositiveIntegerField(_("quantity"), default=1)
    allocated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("allocated by"),
        on_delete=models.SET_NULL,
        null=True,
        related_name="+",
    )
    allocated_at = models.DateTimeField(_("allocated at"), auto_now_add=True)
    handout_note = models.CharField(
        _("hand-out note"), max_length=255, blank=True, help_text=_("E.g. a scratch on the lid.")
    )
    handed_out_at = models.DateTimeField(_("handed out at"), null=True, blank=True)
    returned_at = models.DateTimeField(_("returned at"), null=True, blank=True)

    class Meta:
        verbose_name = _("allocation")
        verbose_name_plural = _("allocations")
        ordering = ["allocated_at", "asset__inventory_number"]

    def __str__(self) -> str:
        target = self.asset or self.consumable
        return f"{self.item.reservation.number}: {target}"

    def clean(self) -> None:
        if bool(self.asset_id) == bool(self.consumable_id):
            raise ValidationError(_("Allocate either a device or a consumable quantity."))
