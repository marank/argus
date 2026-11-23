from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import UUIDModel


class PurchaseOrderLine(UUIDModel):
    order = models.ForeignKey(
        "procurement.PurchaseOrder",
        verbose_name=_("purchase order"),
        on_delete=models.CASCADE,
        related_name="lines",
    )
    asset_model = models.ForeignKey(
        "masterdata.AssetModel",
        verbose_name=_("model"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="order_lines",
    )
    description = models.CharField(_("description"), max_length=255, blank=True)
    quantity = models.PositiveIntegerField(_("quantity"), default=1)
    unit_price = models.DecimalField(_("unit price"), max_digits=10, decimal_places=2, null=True, blank=True)
    quantity_received = models.PositiveIntegerField(_("received quantity"), default=0)
    position = models.PositiveSmallIntegerField(_("position"), default=0)
    asset_request_item = models.ForeignKey(
        "requests.AssetRequestItem",
        verbose_name=_("for request line"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_lines",
    )

    class Meta:
        verbose_name = _("order line")
        verbose_name_plural = _("order lines")
        ordering = ["position"]

    def __str__(self) -> str:
        return f"{self.quantity} × {self.label}"

    def clean(self) -> None:
        if not self.asset_model_id and not self.description:
            raise ValidationError(_("Choose a model or enter a description."))

    @property
    def label(self) -> str:
        return str(self.asset_model) if self.asset_model_id else self.description

    @property
    def quantity_open(self) -> int:
        return max(self.quantity - self.quantity_received, 0)

    @property
    def total(self) -> Decimal:
        return (self.unit_price or Decimal(0)) * self.quantity
