from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Department(TimeStampedModel):
    name = models.CharField(_("name"), max_length=100, unique=True)
    code = models.CharField(_("code"), max_length=20, blank=True)
    cost_center = models.CharField(_("cost center"), max_length=30, blank=True)
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
            "Without approvers such requests go straight to IT."
        ),
    )

    class Meta:
        verbose_name = _("department")
        verbose_name_plural = _("departments")
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name
