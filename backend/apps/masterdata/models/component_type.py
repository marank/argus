from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel

from .category import Category


class ComponentType(TimeStampedModel):
    """A replaceable part tracked on devices, e.g. the *battery* of a scanner or laptop.

    Devices of the assigned categories (and their subcategories) record the serial number of
    the part currently fitted and since when; the service book replaces it.
    """

    name = models.CharField(_("name"), max_length=100, unique=True)
    categories = models.ManyToManyField(
        "masterdata.Category",
        verbose_name=_("categories"),
        blank=True,
        related_name="component_types",
        help_text=_("Devices of these categories and their subcategories have this part."),
    )
    sort_order = models.PositiveIntegerField(_("sort order"), default=0)

    class Meta:
        verbose_name = _("component type")
        verbose_name_plural = _("component types")
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name

    @classmethod
    def for_category(cls, category: Category) -> models.QuerySet[ComponentType]:
        """The parts devices of ``category`` have: assigned to it or to a category above it."""
        ids = [category.pk, *(c.pk for c in category.ancestors())]
        return cls.objects.filter(Q(categories__in=ids)).distinct()
