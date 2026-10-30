from typing import TYPE_CHECKING

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel

if TYPE_CHECKING:
    from .asset import Asset


class License(TimeStampedModel):
    """A purchased software license with a number of seats, e.g. 25 × Microsoft 365.

    Seats are assigned either to employees or to devices, depending on the license.
    """

    class AssignTo(models.TextChoices):
        USER = "user", _("Employees")
        DEVICE = "device", _("Devices")

    model = models.ForeignKey(
        "masterdata.AssetModel",
        verbose_name=_("software"),
        on_delete=models.PROTECT,
        limit_choices_to={"tracking": "license"},
        related_name="licenses",
    )
    reference = models.CharField(
        _("contract / reference"),
        max_length=150,
        blank=True,
        help_text=_("E.g. contract number or agreement, to tell several licenses apart."),
    )
    license_key = models.CharField(_("license key"), max_length=255, blank=True)
    seats = models.PositiveIntegerField(_("seats"), default=1, validators=[MinValueValidator(1)])
    assign_to = models.CharField(
        _("assigned to"), max_length=10, choices=AssignTo.choices, default=AssignTo.USER
    )
    valid_from = models.DateField(_("valid from"), null=True, blank=True)
    valid_until = models.DateField(
        _("valid until"), null=True, blank=True, help_text=_("Leave empty for perpetual licenses.")
    )
    supplier = models.ForeignKey(
        "masterdata.Supplier",
        verbose_name=_("supplier"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="licenses",
    )
    purchase_date = models.DateField(_("purchase date"), null=True, blank=True)
    purchase_price = models.DecimalField(
        _("purchase price"), max_digits=10, decimal_places=2, null=True, blank=True
    )
    notes = models.TextField(_("notes"), blank=True)

    class Meta:
        verbose_name = _("license")
        verbose_name_plural = _("licenses")
        ordering = ["model__name", "valid_until", "created_at"]

    def __str__(self) -> str:
        return f"{self.model} ({self.reference})" if self.reference else str(self.model)

    def clean(self) -> None:
        if self.model_id and not self.model.is_software:
            raise ValidationError({"model": _("Choose a software model.")})
        if self.valid_from and self.valid_until and self.valid_until < self.valid_from:
            raise ValidationError({"valid_until": _("The end date is before the start date.")})

    @property
    def is_expired(self) -> bool:
        return bool(self.valid_until and self.valid_until < timezone.localdate())

    # Set for a request's allocation (apps/requests/schemas/asset_request.py): the device
    # the seat is assigned to. Not a column.
    device: Asset | None


class LicenseAssignment(TimeStampedModel):
    """One seat of a license, used by an employee or a device."""

    license = models.ForeignKey(
        "inventory.License",
        verbose_name=_("license"),
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("employee"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="license_assignments",
    )
    asset = models.ForeignKey(
        "inventory.Asset",
        verbose_name=_("device"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="license_assignments",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("assigned by"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    note = models.CharField(_("note"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("license assignment")
        verbose_name_plural = _("license assignments")
        ordering = ["created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(user__isnull=False, asset__isnull=True)
                | models.Q(user__isnull=True, asset__isnull=False),
                name="license_assignment_user_or_asset",
            ),
            models.UniqueConstraint(
                fields=["license", "user"],
                condition=models.Q(user__isnull=False),
                name="unique_license_user",
            ),
            models.UniqueConstraint(
                fields=["license", "asset"],
                condition=models.Q(asset__isnull=False),
                name="unique_license_asset",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.license} → {self.user or self.asset}"
