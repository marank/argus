from uuid import UUID

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Category(TimeStampedModel):
    """Device group such as *Laptops*, *Headsets* or *MDE accessories*.

    Categories form a tree. Employees request devices by category when the exact
    model does not matter ("I need a headset").
    """

    name = models.CharField(_("name"), max_length=100)
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
    sort_order = models.PositiveIntegerField(_("sort order"), default=0)

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name

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
