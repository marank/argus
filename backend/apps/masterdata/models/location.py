from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Location(TimeStampedModel):
    class Kind(models.TextChoices):
        SITE = "site", _("Site")
        BUILDING = "building", _("Building")
        ROOM = "room", _("Room")
        STORAGE = "storage", _("Storage")

    name = models.CharField(_("name"), max_length=100)
    code = models.CharField(_("code"), max_length=30, blank=True)
    kind = models.CharField(_("kind"), max_length=10, choices=Kind.choices, default=Kind.ROOM)
    parent = models.ForeignKey(
        "self",
        verbose_name=_("parent location"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
    )
    description = models.TextField(_("description"), blank=True)
    is_pickup_point = models.BooleanField(
        _("pickup point"), default=False, help_text=_("Employees can collect devices here.")
    )

    class Meta:
        verbose_name = _("location")
        verbose_name_plural = _("locations")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.full_name

    @property
    def full_name(self) -> str:
        parts, node = [self.name], self.parent
        while node is not None:
            parts.append(node.name)
            node = node.parent
        return " / ".join(reversed(parts))

    def descendant_ids(self) -> set:
        """IDs of this location and all locations below it."""
        ids, frontier = {self.pk}, [self.pk]
        while frontier:
            frontier = list(Location.objects.filter(parent_id__in=frontier).values_list("pk", flat=True))
            ids.update(frontier)
        return ids
