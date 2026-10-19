from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class StockItem(TimeStampedModel):
    """Quantity of a bulk model (ink cartridges, cables, ...) at one location."""

    model = models.ForeignKey(
        "masterdata.AssetModel",
        verbose_name=_("model"),
        on_delete=models.PROTECT,
        related_name="stock_items",
    )
    location = models.ForeignKey(
        "masterdata.Location",
        verbose_name=_("location"),
        on_delete=models.PROTECT,
        related_name="stock_items",
    )
    quantity = models.IntegerField(_("quantity"), default=0)
    reserved_quantity = models.PositiveIntegerField(_("reserved quantity"), default=0)
    min_quantity = models.PositiveIntegerField(
        _("minimum quantity"), default=0, help_text=_("Reorder when the stock falls below.")
    )

    class Meta:
        verbose_name = _("stock item")
        verbose_name_plural = _("stock items")
        ordering = ["model__name"]
        constraints = [
            models.UniqueConstraint(fields=["model", "location"], name="unique_stock_location"),
        ]

    def __str__(self) -> str:
        return f"{self.model} @ {self.location}: {self.quantity}"

    @property
    def available_quantity(self) -> int:
        return max(self.quantity - self.reserved_quantity, 0)

    @property
    def is_below_minimum(self) -> bool:
        return self.quantity < self.min_quantity
