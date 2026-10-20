from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Category(TimeStampedModel):
    """Category such as *Laptops*, *MDE accessories* or *Office software*.

    Categories form a tree and are either hardware or software; subcategories
    share the type of their parent. Employees request by category when the exact
    model does not matter ("I need a headset").
    """

    class Kind(models.TextChoices):
        HARDWARE = "hardware", _("Hardware")
        SOFTWARE = "software", _("Software")

    name = models.CharField(_("name"), max_length=100)
    kind = models.CharField(_("type"), max_length=10, choices=Kind.choices, default=Kind.HARDWARE)
    item_name = models.CharField(
        _("singular name"),
        max_length=100,
        blank=True,
        help_text=_("Name of a single item, e.g. “Laptop”. Shown for “any model” requests."),
    )
    code = models.SlugField(_("code"), max_length=30, unique=True)
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
        help_text=_("Inventory numbers for new assets. Falls back to the parent category."),
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
            "Employees may request “any device” of this group. Turn off where only a "
            "specific model makes sense, e.g. accessories or consumables."
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
    sort_order = models.PositiveIntegerField(_("sort order"), default=0)

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name

    @property
    def is_software(self) -> bool:
        return self.kind == self.Kind.SOFTWARE

    def clean(self) -> None:
        if self.parent_id and self.parent.kind != self.kind:
            raise ValidationError(
                {"kind": _("A subcategory must have the same type as its parent category.")}
            )
        if self.pk and self.children.exclude(kind=self.kind).exists():
            raise ValidationError({"kind": _("Change the type of the subcategories first.")})
        if self.pk and self.kind != Category.objects.get(pk=self.pk).kind:
            if self.asset_models.exists():
                raise ValidationError(
                    {"kind": _("The type cannot be changed while models belong to this category.")}
                )

    def ancestors(self) -> list[Category]:
        chain, node = [], self.parent
        while node is not None:
            chain.append(node)
            node = node.parent
        return chain

    def descendant_ids(self) -> set[UUID]:
        """IDs of this category and all categories below it."""
        ids, frontier = {self.pk}, [self.pk]
        while frontier:
            frontier = list(Category.objects.filter(parent_id__in=frontier).values_list("pk", flat=True))
            ids.update(frontier)
        return ids

    def effective_number_sequence(self):
        for node in [self, *self.ancestors()]:
            if node.number_sequence_id:
                return node.number_sequence
        return None

    def needs_approval(self) -> bool:
        """Whether this category or one above it requires the department's approval."""
        return any(node.requires_approval for node in [self, *self.ancestors()])

    def effective_team(self):
        """The responsible team, inherited from the nearest parent that names one."""
        for node in [self, *self.ancestors()]:
            if node.team_id:
                return node.team
        return None
