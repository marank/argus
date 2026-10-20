from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class AssetIssue(TimeStampedModel):
    """A problem an employee reports for one of their devices; IT handles it."""

    class Kind(models.TextChoices):
        DEFECT = "defect", _("Not working")
        DAMAGE = "damage", _("Damaged")
        LOST = "lost", _("Lost or stolen")
        OTHER = "other", _("Other")

    class Status(models.TextChoices):
        OPEN = "open", _("Open")
        IN_PROGRESS = "in_progress", _("In progress")
        RESOLVED = "resolved", _("Resolved")

    asset = models.ForeignKey(
        "inventory.Asset", verbose_name=_("device"), on_delete=models.CASCADE, related_name="issues"
    )
    kind = models.CharField(_("kind"), max_length=10, choices=Kind.choices, default=Kind.DEFECT)
    description = models.TextField(_("description"))
    status = models.CharField(
        _("status"), max_length=12, choices=Status.choices, default=Status.OPEN, db_index=True
    )
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("reported by"),
        on_delete=models.SET_NULL,
        null=True,
        related_name="reported_issues",
    )
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("handled by"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    # Who is responsible, set on purpose by IT (``handled_by`` is just the last one acting).
    assigned_team = models.ForeignKey(
        "accounts.Team",
        verbose_name=_("team"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issues",
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("assignee"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_issues",
    )
    resolution = models.TextField(_("resolution"), blank=True)
    resolved_at = models.DateTimeField(_("resolved at"), null=True, blank=True)
    # IT changed the status or the resolution since the reporter last looked at their reports.
    unseen_update = models.BooleanField(_("unseen update"), default=False)

    class Meta:
        verbose_name = _("problem report")
        verbose_name_plural = _("problem reports")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.asset}: {self.get_kind_display()}"

    @property
    def is_open(self) -> bool:
        return self.status != self.Status.RESOLVED
