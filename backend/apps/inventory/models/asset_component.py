from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class AssetComponent(TimeStampedModel):
    """The part of a kind currently fitted in a device, e.g. its battery with serial number."""

    asset = models.ForeignKey(
        "inventory.Asset",
        verbose_name=_("asset"),
        on_delete=models.CASCADE,
        related_name="installed_components",
    )
    component_type = models.ForeignKey(
        "masterdata.ComponentType",
        verbose_name=_("component type"),
        on_delete=models.PROTECT,
        related_name="installed",
    )
    serial_number = models.CharField(_("serial number"), max_length=100, blank=True, db_index=True)
    installed_on = models.DateField(_("installed on"), null=True, blank=True)

    class Meta:
        verbose_name = _("installed component")
        verbose_name_plural = _("installed components")
        ordering = ["component_type__sort_order", "component_type__name"]
        constraints = [
            models.UniqueConstraint(fields=["asset", "component_type"], name="unique_asset_component_type")
        ]

    def __str__(self) -> str:
        return f"{self.component_type}: {self.serial_number}"
