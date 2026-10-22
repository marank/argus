from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _

from apps.core.models import UUIDModel


class AssetRequestItem(UUIDModel):
    """One line of a request: *3 × MDE device* or *1 × any headset*.

    Either a category ("any headset") or a specific model is requested. Employees can
    also describe something that is not in the catalog (``description``), optionally
    within a category. IT resolves such free-text lines by assigning a model.
    """

    asset_request = models.ForeignKey(
        "requests.AssetRequest",
        verbose_name=_("request"),
        on_delete=models.CASCADE,
        related_name="items",
    )
    category = models.ForeignKey(
        "masterdata.Category",
        verbose_name=_("category"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    asset_model = models.ForeignKey(
        "masterdata.AssetModel",
        verbose_name=_("model"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    description = models.CharField(
        _("description"),
        max_length=255,
        blank=True,
        help_text=_("Free text for something that is not in the catalog."),
    )
    quantity_requested = models.PositiveIntegerField(_("requested quantity"), default=1)
    quantity_confirmed = models.PositiveIntegerField(_("confirmed quantity"), null=True, blank=True)
    note = models.CharField(_("note"), max_length=255, blank=True)
    # UUIDs carry no order, so lines keep the order in which they were requested.
    position = models.PositiveSmallIntegerField(_("position"), default=0)

    class Meta:
        verbose_name = _("request line")
        verbose_name_plural = _("request lines")
        ordering = ["position"]

    def __str__(self) -> str:
        return f"{self.quantity_requested} × {self.label}"

    def clean(self) -> None:
        if not self.category_id and not self.asset_model_id and not self.description.strip():
            raise ValidationError(_("Choose a category or a model, or describe what you need."))

    @property
    def is_free_text(self) -> bool:
        """Free-text line that IT has not yet mapped to a model."""
        return bool(self.description) and not self.asset_model_id

    @property
    def label(self) -> str:
        if self.asset_model_id:
            return str(self.asset_model)
        if self.description:
            return f"{self.category}: {self.description}" if self.category_id else self.description
        return str(self.category)

    @property
    def requires_approval(self) -> bool:
        category = self.asset_model.category if self.asset_model_id else self.category
        return category.needs_approval() if category else False

    @property
    def effective_category_id(self) -> int:
        return self.asset_model.category_id if self.asset_model_id else self.category_id

    @property
    def quantity_target(self) -> int:
        """The quantity IT committed to, or the requested quantity before IT confirmed it."""
        if self.quantity_confirmed is None:
            return self.quantity_requested
        return self.quantity_confirmed

    @property
    def quantity_allocated(self) -> int:
        cached = getattr(self, "_quantity_allocated", None)
        if cached is not None:
            return cached
        return self.allocations.aggregate(total=Sum("quantity"))["total"] or 0

    @property
    def is_software(self) -> bool:
        """Software lines are filled with license seats instead of devices."""
        if self.asset_model_id:
            return self.asset_model.is_software
        return bool(self.category_id and self.category.is_software)

    @property
    def quantity_missing(self) -> int:
        return max(self.quantity_target - self.quantity_allocated, 0)
