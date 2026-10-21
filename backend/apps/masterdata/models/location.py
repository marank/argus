from django.core.exceptions import ValidationError
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

    def clean(self) -> None:
        # The UUID is set on creation, so ``self.pk`` does not tell a new location apart.
        if not self._state.adding and self.parent_id and self.parent_id in self.descendant_ids():
            raise ValidationError(
                {"parent": _("A location cannot be placed inside itself or one of its sub-locations.")}
            )

    @property
    def full_name(self) -> str:
        parts, seen, node = [self.name], {self.pk}, self.parent
        # The seen set stops at a loop in the tree, should one ever get into the database.
        while node is not None and node.pk not in seen:
            seen.add(node.pk)
            parts.append(node.name)
            node = node.parent
        return " / ".join(reversed(parts))

    def descendant_ids(self) -> set:
        """IDs of this location and all locations below it."""
        # One query for the whole (small) tree instead of one per level.
        children: dict = {}
        for pk, parent_id in Location.objects.filter(parent__isnull=False).values_list("pk", "parent_id"):
            children.setdefault(parent_id, []).append(pk)
        ids, frontier = {self.pk}, [self.pk]
        while frontier:
            frontier = [pk for parent in frontier for pk in children.get(parent, []) if pk not in ids]
            ids.update(frontier)
        return ids
