from uuid import UUID

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Department(TimeStampedModel):
    """Department employees work in, such as *Operations* with *Logistics* and *Support* below it.

    Departments form a tree; a department without approvers of its own takes over
    those of the nearest department above it that has some.
    """

    name = models.CharField(_("name"), max_length=100, unique=True)
    code = models.CharField(_("code"), max_length=20, blank=True)
    cost_center = models.CharField(_("cost center"), max_length=30, blank=True)
    parent = models.ForeignKey(
        "self",
        verbose_name=_("parent department"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
    )
    sort_order = models.PositiveIntegerField(
        _("sort order"), default=0, help_text=_("Lower numbers come first; equal numbers by name.")
    )
    approvers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name=_("approvers"),
        blank=True,
        related_name="approving_departments",
        help_text=_(
            "Approve requests of the department's members for categories that need approval. "
            "Without approvers those of the parent department apply; without any, "
            "such requests go straight to IT."
        ),
    )

    class Meta:
        verbose_name = _("department")
        verbose_name_plural = _("departments")
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        # The UUID is set on creation, so ``self.pk`` does not tell a new department apart.
        if not self._state.adding and self.parent_id and self.parent_id in self.descendant_ids():
            raise ValidationError(
                {"parent": _("A department cannot be placed below itself or one of its subdepartments.")}
            )

    def ancestors(self) -> list[Department]:
        chain, node = [], self.parent
        # The pk check stops at a loop in the tree, should one ever get into the database.
        while node is not None and node.pk != self.pk and node not in chain:
            chain.append(node)
            node = node.parent
        return chain

    def descendant_ids(self) -> set[UUID]:
        """IDs of this department and all departments below it."""
        # One query for the whole (small) tree instead of one per level.
        children: dict = {}
        for pk, parent_id in Department.objects.filter(parent__isnull=False).values_list("pk", "parent_id"):
            children.setdefault(parent_id, []).append(pk)
        ids, frontier = {self.pk}, [self.pk]
        while frontier:
            frontier = [pk for parent in frontier for pk in children.get(parent, []) if pk not in ids]
            ids.update(frontier)
        return ids

    @classmethod
    def tree_positions(cls) -> dict[UUID, int]:
        """Position of every department in the tree read top-down: each department, then
        the ones below it; siblings by sort order and name."""
        rows = list(cls.objects.values_list("pk", "parent_id", "sort_order", "name"))
        children: dict = {}
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
        # Departments caught in a loop have no way up to a root; they come last.
        for pk, *_ in rows:
            positions.setdefault(pk, len(positions))
        return positions

    @classmethod
    def approval_sources(cls) -> dict[UUID, UUID | None]:
        """For every department, the one whose approvers decide: the department itself
        when it has active approvers, otherwise the nearest one above that has some."""
        parents = dict(cls.objects.values_list("pk", "parent_id"))
        with_approvers = set(
            cls.objects.filter(approvers__is_active=True).values_list("pk", flat=True).distinct()
        )
        sources: dict[UUID, UUID | None] = {}
        for pk in parents:
            node, seen = pk, set()
            # The seen set stops at a loop in the tree, should one ever get into the database.
            while node is not None and node not in with_approvers and node not in seen:
                seen.add(node)
                node = parents.get(node)
            sources[pk] = node if node in with_approvers else None
        return sources

    def approval_source(self) -> Department | None:
        """The department whose approvers decide for this one (see ``approval_sources``)."""
        for node in [self, *self.ancestors()]:
            if node.approvers.filter(is_active=True).exists():
                return node
        return None
