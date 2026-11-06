from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class AssetEventKind(models.TextChoices):
    CREATED = "created", _("Created")
    STATUS_CHANGED = "status_changed", _("Status changed")
    ASSIGNED = "assigned", _("Handed out")
    RETURNED = "returned", _("Returned")
    RESERVED = "reserved", _("Reserved")
    COMPONENT_REPLACED = "component_replaced", _("Component replaced")
    REPAIR = "repair", _("Repair")
    MAINTENANCE = "maintenance", _("Maintenance")
    INSPECTION = "inspection", _("Inspection")
    NOTE = "note", _("Note")
    ISSUE_REPORTED = "issue_reported", _("Problem reported")
    ISSUE_RESOLVED = "issue_resolved", _("Problem resolved")


class AssetEvent(TimeStampedModel):
    """Entry in the life cycle log of an asset (part replaced, repair, hand-out, ...)."""

    # Kinds a technician records manually; the others are written by workflows.
    MANUAL_KINDS = (
        AssetEventKind.COMPONENT_REPLACED,
        AssetEventKind.REPAIR,
        AssetEventKind.MAINTENANCE,
        AssetEventKind.INSPECTION,
        AssetEventKind.NOTE,
    )

    asset = models.ForeignKey(
        "inventory.Asset", verbose_name=_("asset"), on_delete=models.CASCADE, related_name="events"
    )
    kind = models.CharField(_("kind"), max_length=20, choices=AssetEventKind.choices, db_index=True)
    occurred_at = models.DateTimeField(_("occurred at"), default=timezone.now)
    description = models.TextField(_("description"), blank=True)
    component = models.CharField(_("component"), max_length=100, blank=True)
    component_serial = models.CharField(_("component serial number"), max_length=100, blank=True)
    # A replaced part of a tracked kind (see ComponentType): the device gets component_serial.
    component_type = models.ForeignKey(
        "masterdata.ComponentType",
        verbose_name=_("component type"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    previous_serial = models.CharField(_("previous serial number"), max_length=100, blank=True)
    cost = models.DecimalField(_("cost"), max_digits=10, decimal_places=2, null=True, blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("performed by"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    related_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("employee"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asset_events",
    )
    asset_request = models.ForeignKey(
        "requests.AssetRequest",
        verbose_name=_("request"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asset_events",
    )

    class Meta:
        verbose_name = _("asset event")
        verbose_name_plural = _("asset events")
        ordering = ["-occurred_at", "-created_at"]

    def __str__(self) -> str:
        return f"{self.asset.inventory_number}: {self.get_kind_display()}"
