from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class PurchaseOrder(TimeStampedModel):
    """Tracks what has to be ordered, what was ordered and what has arrived."""

    class Status(models.TextChoices):
        DRAFT = "draft", _("To order")
        ORDERED = "ordered", _("Ordered")
        PARTIALLY_RECEIVED = "partially_received", _("Partially received")
        RECEIVED = "received", _("Received")
        CANCELLED = "cancelled", _("Cancelled")

    OPEN_STATUSES = (Status.DRAFT, Status.ORDERED, Status.PARTIALLY_RECEIVED)

    number = models.CharField(_("number"), max_length=30, unique=True, blank=True)
    supplier = models.ForeignKey(
        "masterdata.Supplier",
        verbose_name=_("supplier"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="purchase_orders",
    )
    status = models.CharField(
        _("status"), max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    order_date = models.DateField(_("order date"), null=True, blank=True)
    expected_date = models.DateField(_("expected delivery"), null=True, blank=True)
    supplier_reference = models.CharField(_("supplier reference"), max_length=100, blank=True)
    delivery_location = models.ForeignKey(
        "masterdata.Location",
        verbose_name=_("delivery location"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    notes = models.TextField(_("notes"), blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("created by"),
        on_delete=models.SET_NULL,
        null=True,
        related_name="+",
    )

    class Meta:
        verbose_name = _("purchase order")
        verbose_name_plural = _("purchase orders")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.number

    def save(self, *args, **kwargs):
        if not self.number:
            from apps.core.services.numbering import next_number

            self.number = next_number(
                "purchase-order", taken=lambda n: PurchaseOrder.objects.filter(number=n).exists()
            )
        super().save(*args, **kwargs)

    @property
    def total(self) -> Decimal:
        return sum((line.total for line in self.lines.all()), Decimal("0"))
