from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import UUIDModel


class ActivityArea(models.TextChoices):
    """Where a step happened; the values are the permission resources (``ResourceKey``)."""

    REQUESTS = "requests", _("Requests")
    ASSETS = "assets", _("Devices")
    CONSUMABLES = "consumables", _("Consumables")
    LICENSES = "licenses", _("Licenses")
    ISSUES = "issues", _("Problem reports")
    PROCUREMENT = "procurement", _("Orders")


class ActivityKind(models.TextChoices):
    REQUEST_CREATED = "request_created", _("Requested")
    REQUEST_DIRECT = "request_direct", _("Direct hand-out recorded")
    REQUEST_QUICK = "request_quick", _("Quick assignment recorded")
    REQUEST_APPROVED = "request_approved", _("Approved")
    REQUEST_DECLINED = "request_declined", _("Not approved")
    REQUEST_CONFIRMED = "request_confirmed", _("Confirmed")
    REQUEST_REJECTED = "request_rejected", _("Rejected")
    REQUEST_CANCELLED = "request_cancelled", _("Cancelled")
    REQUEST_REPLACED = "request_replaced", _("Replaced")
    REQUEST_ASSIGNED = "request_assigned", _("Assignment changed")
    REQUEST_ALLOCATED = "request_allocated", _("Allocated")
    REQUEST_READY = "request_ready", _("Ready for pickup")
    REQUEST_REOPENED = "request_reopened", _("Back in preparation")
    REQUEST_RESCHEDULED = "request_rescheduled", _("Handover changed")
    REQUEST_HANDED_OUT = "request_handed_out", _("Handed out")
    REQUEST_RETURNED = "request_returned", _("Taken back")
    REQUEST_EXTENDED = "request_extended", _("Loan extended")
    REQUEST_REMINDED = "request_reminded", _("Reminded to return")
    REQUEST_COMPLETED = "request_completed", _("Completed")
    ASSET_CREATED = "asset_created", _("Device created")
    ASSETS_CREATED = "assets_created", _("Devices created")
    ASSETS_IMPORTED = "assets_imported", _("Devices imported")
    ASSET_STATUS_CHANGED = "asset_status_changed", _("Status changed")
    ASSET_ASSIGNED = "asset_assigned", _("Handed out")
    ASSET_RETURNED = "asset_returned", _("Returned")
    ASSET_REPLACED = "asset_replaced", _("Device replaced")
    ASSET_COMPONENT_REPLACED = "asset_component_replaced", _("Component replaced")
    ASSET_REPAIR = "asset_repair", _("Repair")
    ASSET_MAINTENANCE = "asset_maintenance", _("Maintenance")
    ASSET_INSPECTION = "asset_inspection", _("Inspection")
    ASSET_NOTE = "asset_note", _("Note")
    ASSET_EVENT_DELETED = "asset_event_deleted", _("History entry deleted")
    ASSET_DELETED = "asset_deleted", _("Device deleted")
    ISSUE_REPORTED = "issue_reported", _("Problem reported")
    ISSUE_IN_PROGRESS = "issue_in_progress", _("Report taken into work")
    ISSUE_REOPENED = "issue_reopened", _("Report reopened")
    ISSUE_RESOLVED = "issue_resolved", _("Problem resolved")
    CONSUMABLE_RECEIPT = "consumable_receipt", _("Stock received")
    CONSUMABLE_ISSUE = "consumable_issue", _("Stock issued")
    CONSUMABLE_RETURN = "consumable_return", _("Stock returned")
    CONSUMABLE_ADJUSTMENT = "consumable_adjustment", _("Stock corrected")
    CONSUMABLE_CONSUMPTION = "consumable_consumption", _("Stock consumed")
    LICENSE_CREATED = "license_created", _("License created")
    LICENSE_DELETED = "license_deleted", _("License deleted")
    LICENSE_ASSIGNED = "license_assigned", _("Seat assigned")
    LICENSE_UNASSIGNED = "license_unassigned", _("Seat removed")
    ORDER_CREATED = "order_created", _("Order created")
    ORDER_PLACED = "order_placed", _("Ordered")
    ORDER_RECEIVED = "order_received", _("Delivery received")
    ORDER_CANCELLED = "order_cancelled", _("Order cancelled")
    ORDER_DELETED = "order_deleted", _("Order deleted")


class Activity(UUIDModel):
    """One step of IT's daily work, across all areas: who did what, when, to what.

    A step that touches several devices (a hand-out, a delivery) is one row. The label
    of the object is kept as text, so the row stays readable after the object is deleted.
    """

    occurred_at = models.DateTimeField(_("occurred at"), default=timezone.now, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("performed by"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    area = models.CharField(_("area"), max_length=20, choices=ActivityArea.choices)
    kind = models.CharField(_("kind"), max_length=30, choices=ActivityKind.choices)
    subject_id = models.UUIDField(_("object"), null=True, blank=True)
    subject_label = models.CharField(_("object"), max_length=300)
    related_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("employee"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    # Devices or items of the step, or the change in stock (negative when booked out).
    quantity = models.IntegerField(_("quantity"), null=True, blank=True)
    detail = models.TextField(_("detail"), blank=True)

    class Meta:
        verbose_name = _("activity")
        verbose_name_plural = _("activities")
        ordering = ["-occurred_at", "-id"]
        indexes = [models.Index(fields=["area", "-occurred_at"], name="activity_area_time")]

    def __str__(self) -> str:
        return f"{self.subject_label}: {self.get_kind_display()}"
