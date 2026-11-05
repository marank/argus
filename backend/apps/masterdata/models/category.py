from typing import TYPE_CHECKING
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel

if TYPE_CHECKING:
    from apps.accounts.models import Team

    from .asset_model import AssetModel


class CategoryKind(models.TextChoices):
    HARDWARE = "hardware", _("Hardware")
    SOFTWARE = "software", _("Software")


class Category(TimeStampedModel):
    """Category such as *Laptops*, *MDE accessories* or *Office software*.

    Categories form a tree and are either hardware or software; subcategories
    share the type of their parent. Employees request by category when the exact
    model does not matter ("I need a headset").
    """

    name = models.CharField(_("name"), max_length=100)
    kind = models.CharField(
        _("type"), max_length=10, choices=CategoryKind.choices, default=CategoryKind.HARDWARE
    )
    item_name = models.CharField(
        _("singular name"),
        max_length=100,
        blank=True,
        help_text=_("Name of a single item, e.g. “Laptop”. Shown for “any model” requests."),
    )
    code = models.SlugField(_("code"), max_length=30, blank=True)
    parent = models.ForeignKey(
        "self",
        verbose_name=_("parent category"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
    )
    description = models.TextField(_("description"), blank=True)
    icon = models.CharField(_("icon"), max_length=50, blank=True, help_text=_("Icon name"))
    number_sequence = models.ForeignKey(
        "core.NumberSequence",
        verbose_name=_("number sequence"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="categories",
        help_text=_(
            "Inventory numbers for new assets. Not inherited by subcategories; "
            "without one, the general asset sequence applies."
        ),
    )
    team = models.ForeignKey(
        "accounts.Team",
        verbose_name=_("responsible team"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="categories",
        help_text=_("New requests and reports for this category go to this team. Falls back to the parent."),
    )
    is_requestable = models.BooleanField(
        _("requestable"), default=True, help_text=_("Shown in the employee portal.")
    )
    allow_any_model = models.BooleanField(
        _("any model requestable"),
        default=True,
        help_text=_(
            "Employees may request “any model” of this category, e.g. a charging cable "
            "when the type does not matter; IT picks the model when assigning. Turn off "
            "where employees have to choose a specific model."
        ),
    )
    requires_approval = models.BooleanField(
        _("requires approval"),
        default=False,
        help_text=_(
            "Requests must first be approved by the employee's department. "
            "Applies to the subcategories as well."
        ),
    )
    is_accessory = models.BooleanField(
        _("accessories"),
        default=False,
        help_text=_(
            "Holds accessories, spare parts or consumables. In the employee portal its models "
            "appear with the devices they are compatible with. Applies to the subcategories as well."
        ),
    )
    sort_order = models.PositiveIntegerField(_("sort order"), default=0)

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")
        ordering = ["sort_order", "name"]
        constraints = [
            # The code is optional; given codes stay unique.
            models.UniqueConstraint(
                fields=["code"],
                condition=~models.Q(code=""),
                name="unique_category_code",
                violation_error_message=_("A category with this code already exists."),
                # Reported at the code field rather than for the whole form.
                violation_error_code="unique",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def is_software(self) -> bool:
        return self.kind == CategoryKind.SOFTWARE

    def clean(self) -> None:
        # The UUID is set on creation, so ``self.pk`` does not tell a new category apart.
        saved = not self._state.adding
        if saved and self.parent_id and self.parent_id in self.descendant_ids():
            raise ValidationError(
                {"parent": _("A category cannot be placed below itself or one of its subcategories.")}
            )
        if self.parent is not None and self.parent.kind != self.kind:
            raise ValidationError(
                {"kind": _("A subcategory must have the same type as its parent category.")}
            )
        if saved and self.children.exclude(kind=self.kind).exists():
            raise ValidationError({"kind": _("Change the type of the subcategories first.")})
        if saved and self.kind != Category.objects.get(pk=self.pk).kind:
            if self.asset_models.exists():
                raise ValidationError(
                    {"kind": _("The type cannot be changed while models belong to this category.")}
                )

    def ancestors(self) -> list[Category]:
        chain, node = [], self.parent
        # The pk check stops at a loop in the tree, should one ever get into the database.
        while node is not None and node.pk != self.pk and node not in chain:
            chain.append(node)
            node = node.parent
        return chain

    def descendant_ids(self) -> set[UUID]:
        """IDs of this category and all categories below it."""
        # One query for the whole (small) tree instead of one per level.
        children: dict[UUID, list[UUID]] = {}
        for pk, parent_id in Category.objects.filter(parent__isnull=False).values_list("pk", "parent_id"):
            children.setdefault(parent_id, []).append(pk)
        ids, frontier = {self.pk}, [self.pk]
        while frontier:
            frontier = [pk for parent in frontier for pk in children.get(parent, []) if pk not in ids]
            ids.update(frontier)
        return ids

    @classmethod
    def tree_positions(cls) -> dict[UUID, int]:
        """Position of every category in the tree read top-down: each category, then the
        ones below it; siblings by sort order and name."""
        rows = list(cls.objects.values_list("pk", "parent_id", "sort_order", "name"))
        children: dict[UUID | None, list[tuple[int, str, UUID]]] = {}
        for pk, parent_id, sort_order, name in rows:
            children.setdefault(parent_id, []).append((sort_order, name.lower(), pk))
        positions: dict[UUID, int] = {}
        stack = sorted(children.get(None, []), reverse=True)
        while stack:
            *_, pk = stack.pop()
            if pk in positions:
                continue
            positions[pk] = len(positions)
            stack.extend(sorted(children.get(pk, []), reverse=True))
        # Categories caught in a loop have no way up to a root; they come last.
        for pk, *_ in rows:
            positions.setdefault(pk, len(positions))
        return positions

    def needs_approval(self) -> bool:
        """Whether this category or one above it requires the department's approval."""
        return any(node.requires_approval for node in [self, *self.ancestors()])

    def holds_accessories(self) -> bool:
        """Whether this category or one above it is marked as holding accessories."""
        return any(node.is_accessory for node in [self, *self.ancestors()])

    def effective_team(self) -> Team | None:
        """The responsible team, inherited from the nearest parent that names one."""
        for node in [self, *self.ancestors()]:
            if node.team_id:
                return node.team
        return None

    # Set by the portal catalog (apps/requests/api/portal.py), not columns. Declared
    # last: above the fields, "models" would shadow django.db.models in this class body.
    models: list[AssetModel]
    available: int | None
    reserved: int | None
    in_accessory_tree: bool
