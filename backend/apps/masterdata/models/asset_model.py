from typing import TYPE_CHECKING
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel

if TYPE_CHECKING:
    from apps.accounts.models import Team
    from apps.core.models import NumberSequence


class AssetModel(TimeStampedModel):
    """A concrete product, e.g. *Lenovo ThinkPad T14 Gen 5* or *HP 305 black*.

    ``SERIALIZED`` models are tracked as individual assets with serial numbers;
    ``BULK`` models (ink cartridges, cables, ...) are tracked as consumables with quantities;
    ``LICENSE`` models are software products (in software categories) tracked as licenses.
    """

    class Tracking(models.TextChoices):
        SERIALIZED = "serialized", _("Individual devices")
        BULK = "bulk", _("Consumable (quantity)")
        LICENSE = "license", _("Software license")

    # Several models may share a name; the manufacturer's designation tells them apart.
    name = models.CharField(_("name"), max_length=150)
    designation = models.CharField(
        _("manufacturer designation"),
        max_length=150,
        help_text=_("The model as the manufacturer calls it; unique per manufacturer."),
    )
    manufacturer = models.ForeignKey(
        "masterdata.Manufacturer",
        verbose_name=_("manufacturer"),
        on_delete=models.PROTECT,
        related_name="asset_models",
    )
    category = models.ForeignKey(
        "masterdata.Category",
        verbose_name=_("category"),
        on_delete=models.PROTECT,
        related_name="asset_models",
    )
    part_number = models.CharField(_("part number"), max_length=100, blank=True)
    ean = models.CharField(_("EAN / GTIN"), max_length=14, blank=True, db_index=True)
    tracking = models.CharField(
        _("tracking"), max_length=12, choices=Tracking.choices, default=Tracking.SERIALIZED
    )
    description = models.TextField(_("description"), blank=True)
    specifications = models.TextField(_("specifications"), blank=True)
    default_supplier = models.ForeignKey(
        "masterdata.Supplier",
        verbose_name=_("default supplier"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asset_models",
    )
    list_price = models.DecimalField(_("list price"), max_digits=10, decimal_places=2, null=True, blank=True)
    warranty_months = models.PositiveSmallIntegerField(_("warranty (months)"), default=24)
    compatible_with = models.ManyToManyField(
        "self",
        verbose_name=_("compatible with"),
        blank=True,
        help_text=_("Accessories, spare parts and consumables that fit this model."),
    )
    predecessor = models.ForeignKey(
        "self",
        verbose_name=_("successor of"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="successors",
        help_text=_("The model this one replaces."),
    )
    number_sequence = models.ForeignKey(
        "core.NumberSequence",
        verbose_name=_("number sequence"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asset_models",
        help_text=_(
            "Inventory numbers for new devices of this model. Empty: the category's sequence, "
            "otherwise the general asset sequence."
        ),
    )
    team = models.ForeignKey(
        "accounts.Team",
        verbose_name=_("responsible team"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asset_models",
        help_text=_("New requests and reports for this model go to this team. Empty: as the category."),
    )
    is_requestable = models.BooleanField(_("requestable"), default=True)
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        verbose_name = _("model")
        verbose_name_plural = _("models")
        ordering = ["manufacturer__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["manufacturer", "designation"],
                name="unique_model_designation",
                violation_error_message=_("This manufacturer already has a model with this designation."),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.manufacturer} {self.name}"

    @property
    def full_name(self) -> str:
        return f"{self.manufacturer.name} {self.name}"

    @property
    def is_bulk(self) -> bool:
        return self.tracking == self.Tracking.BULK

    def effective_team(self) -> Team | None:
        """The responsible team: the model's own, otherwise the category's."""
        return self.team if self.team_id else self.category.effective_team()

    def effective_number_sequence(self) -> NumberSequence | None:
        """The sequence for new devices: the model's own, otherwise the category's (None = general)."""
        return self.number_sequence if self.number_sequence_id else self.category.number_sequence

    @property
    def is_software(self) -> bool:
        return self.tracking == self.Tracking.LICENSE

    def clean(self) -> None:
        # A new, unsaved form has no category yet; django-stubs types the column as always set.
        if self.category_id is not None and self.category.is_software != self.is_software:  # type: ignore[comparison-overlap, redundant-expr]
            raise ValidationError(
                {
                    "tracking": _(
                        "Software categories only take licenses; licenses only belong to software categories."
                    )
                }
            )
        if self.predecessor_id and self.predecessor_id in self._successor_chain_ids():
            raise ValidationError(
                {"predecessor": _("A model cannot succeed itself or one of its successors.")}
            )

    def _successor_chain_ids(self) -> set[UUID]:
        """IDs of this model and of all models that (indirectly) succeed it."""
        successors: dict[UUID, list[UUID]] = {}
        for pk, predecessor_id in AssetModel.objects.filter(predecessor__isnull=False).values_list(
            "pk", "predecessor_id"
        ):
            successors.setdefault(predecessor_id, []).append(pk)
        ids, frontier = {self.pk}, [self.pk]
        while frontier:
            frontier = [pk for model in frontier for pk in successors.get(model, []) if pk not in ids]
            ids.update(frontier)
        return ids

    # Set by the portal catalog (apps/requests/api/portal.py), not columns; declared last
    # so the names shadow nothing in the class body.
    available: int | None
    reserved: int | None
    accessories: list[UUID]
