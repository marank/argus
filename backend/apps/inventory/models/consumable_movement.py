from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class ConsumableMovement(TimeStampedModel):
    class Reason(models.TextChoices):
        RECEIPT = "receipt", _("Goods receipt")
        ISSUE = "issue", _("Issue")
        RETURN = "return", _("Return")
        ADJUSTMENT = "adjustment", _("Adjustment")
        CONSUMPTION = "consumption", _("Used for repair")

    consumable = models.ForeignKey(
        "inventory.Consumable",
        verbose_name=_("consumable"),
        on_delete=models.CASCADE,
        related_name="movements",
    )
    delta = models.IntegerField(_("change"))
    reason = models.CharField(_("reason"), max_length=12, choices=Reason.choices)
    note = models.CharField(_("note"), max_length=255, blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("performed by"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("recipient"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consumable_movements",
    )
    reservation = models.ForeignKey(
        "reservations.Reservation",
        verbose_name=_("reservation"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consumable_movements",
    )
    purchase_order_line = models.ForeignKey(
        "procurement.PurchaseOrderLine",
        verbose_name=_("purchase order line"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consumable_movements",
    )

    class Meta:
        verbose_name = _("consumable movement")
        verbose_name_plural = _("consumable movements")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.consumable.model}: {self.delta:+d}"
