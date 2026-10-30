from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel

if TYPE_CHECKING:
    from apps.masterdata.models import AssetModel


class AssetStatus(models.TextChoices):
    IN_STOCK = "in_stock", _("In stock")
    RESERVED = "reserved", _("Reserved")
    IN_USE = "in_use", _("In use")
    IN_REPAIR = "in_repair", _("In repair")
    LOST = "lost", _("Lost")
    RETIRED = "retired", _("Retired")


class Asset(TimeStampedModel):
    """A single, individually tracked device (laptop, phone, MDE, headset, ...)."""

    class Condition(models.TextChoices):
        NEW = "new", _("New")
        GOOD = "good", _("Good")
        WORN = "worn", _("Worn")
        DEFECTIVE = "defective", _("Defective")

    inventory_number = models.CharField(_("inventory number"), max_length=50, unique=True, blank=True)
    model = models.ForeignKey(
        "masterdata.AssetModel",
        verbose_name=_("model"),
        on_delete=models.PROTECT,
        related_name="assets",
    )
    serial_number = models.CharField(_("serial number"), max_length=100, blank=True, db_index=True)
    imei = models.CharField(_("IMEI"), max_length=20, blank=True)
    mac_address = models.CharField(_("MAC address"), max_length=17, blank=True)
    hostname = models.CharField(_("hostname"), max_length=63, blank=True)

    status = models.CharField(
        _("status"), max_length=12, choices=AssetStatus.choices, default=AssetStatus.IN_STOCK, db_index=True
    )
    condition = models.CharField(
        _("condition"), max_length=10, choices=Condition.choices, default=Condition.NEW
    )
    is_loanable = models.BooleanField(
        _("loanable"), default=True, help_text=_("Part of the pool employees can reserve from.")
    )
    location = models.ForeignKey(
        "masterdata.Location",
        verbose_name=_("location"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assets",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("assigned to"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="assets",
    )
    assigned_since = models.DateTimeField(_("assigned since"), null=True, blank=True)
    parent = models.ForeignKey(
        "self",
        verbose_name=_("belongs to"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="components",
        help_text=_("E.g. a docking station or handle that belongs to another device."),
    )

    supplier = models.ForeignKey(
        "masterdata.Supplier",
        verbose_name=_("supplier"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assets",
    )
    purchase_order_line = models.ForeignKey(
        "procurement.PurchaseOrderLine",
        verbose_name=_("purchase order line"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assets",
    )
    purchase_date = models.DateField(_("purchase date"), null=True, blank=True)
    purchase_price = models.DecimalField(
        _("purchase price"), max_digits=10, decimal_places=2, null=True, blank=True
    )
    warranty_until = models.DateField(_("warranty until"), null=True, blank=True)
    consumables = models.ManyToManyField(
        "masterdata.AssetModel",
        verbose_name=_("consumables"),
        blank=True,
        limit_choices_to={"tracking": "bulk"},
        related_name="consuming_assets",
        help_text=_("Consumables for this device in addition to those compatible with its model."),
    )
    notes = models.TextField(_("notes"), blank=True)

    def consumable_models(self) -> models.QuerySet[AssetModel]:
        """Consumables for this device: its own plus those compatible with its model."""
        from apps.masterdata.models import AssetModel

        return AssetModel.objects.filter(
            models.Q(consuming_assets=self) | models.Q(compatible_with=self.model_id),
            tracking=AssetModel.Tracking.BULK,
        ).distinct()

    class Meta:
        verbose_name = _("asset")
        verbose_name_plural = _("assets")
        ordering = ["inventory_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["model", "serial_number"],
                condition=~models.Q(serial_number=""),
                name="unique_serial_per_model",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.inventory_number} – {self.model}"

    def clean(self) -> None:
        from apps.masterdata.models import AssetModel

        if self.model_id and self.model.tracking != AssetModel.Tracking.SERIALIZED:
            raise ValidationError(
                {"model": _("Only models tracked as individual devices can be added as devices.")}
            )

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.inventory_number:
            from apps.core.services.numbering import next_number

            sequence = self.model.effective_number_sequence() or "asset"
            self.inventory_number = next_number(
                sequence, taken=lambda n: Asset.objects.filter(inventory_number=n).exists()
            )
        super().save(*args, **kwargs)
