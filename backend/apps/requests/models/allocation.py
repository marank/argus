from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import UUIDModel


class AssetRequestAllocation(UUIDModel):
    """A concrete device, consumable quantity or license seat set aside for a request line.

    License seats are assigned (``license_assignment``) as soon as they are allocated;
    the assignment is removed again when the allocation is released or returned.
    """

    item = models.ForeignKey(
        "requests.AssetRequestItem",
        verbose_name=_("request line"),
        on_delete=models.CASCADE,
        related_name="allocations",
    )
    asset = models.ForeignKey(
        "inventory.Asset",
        verbose_name=_("asset"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="asset_request_allocations",
    )
    consumable = models.ForeignKey(
        "inventory.Consumable",
        verbose_name=_("consumable"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="asset_request_allocations",
    )
    license = models.ForeignKey(
        "inventory.License",
        verbose_name=_("license"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="asset_request_allocations",
    )
    license_assignment = models.OneToOneField(
        "inventory.LicenseAssignment",
        verbose_name=_("license assignment"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asset_request_allocation",
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
    device_return = models.ForeignKey(
        "requests.DeviceReturn",
        verbose_name=_("return"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="allocations",
    )
    returned_damaged = models.BooleanField(_("returned damaged"), default=False)
    return_note = models.CharField(
        _("return note"), max_length=255, blank=True, help_text=_("E.g. the condition when it came back.")
    )

    class Meta:
        verbose_name = _("allocation")
        verbose_name_plural = _("allocations")
        ordering = ["allocated_at", "asset__inventory_number"]

    def __str__(self) -> str:
        target = self.asset or self.consumable or self.license
        return f"{self.item.asset_request.number}: {target}"

    @property
    def model(self):
        """The catalog model of what was allocated."""
        if self.asset:
            return self.asset.model
        if self.consumable:
            return self.consumable.model
        assert self.license is not None  # clean(): exactly one of asset, consumable, license
        return self.license.model

    @property
    def is_returnable(self) -> bool:
        """Devices and license seats come back; consumables are used up."""
        return bool(self.asset_id or self.license_id)

    def clean(self) -> None:
        if sum(bool(x) for x in (self.asset_id, self.consumable_id, self.license_id)) != 1:
            raise ValidationError(_("Allocate either a device, a consumable quantity or a license seat."))
