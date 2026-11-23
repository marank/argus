from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import UUIDModel


class AssetRequestEventKind(models.TextChoices):
    CREATED = "created", _("Requested")
    DIRECT = "direct", _("Direct hand-out recorded")
    QUICK = "quick", _("Quick assignment recorded")
    APPROVED = "approved", _("Approved")
    DECLINED = "declined", _("Not approved")
    CONFIRMED = "confirmed", _("Confirmed")
    REJECTED = "rejected", _("Rejected")
    CANCELLED = "cancelled", _("Cancelled")
    REPLACED = "replaced", _("Replaced")
    ASSIGNED = "assigned", _("Assignment changed")
    ALLOCATED = "allocated", _("Allocated")
    RELEASED = "released", _("Allocation removed")
    READY = "ready", _("Preparation finished")
    REOPENED = "reopened", _("Back in preparation")
    RESCHEDULED = "rescheduled", _("Handover changed")
    HANDED_OUT = "handed_out", _("Handed out")
    RETURNED = "returned", _("Taken back")
    EXTENDED = "extended", _("Loan extended")
    REMINDED = "reminded", _("Reminded to return")
    COMPLETED = "completed", _("Completed")


class AssetRequestEvent(UUIDModel):
    """One step in the history of a request: who did what, when.

    Written by the workflow as it happens. ``data`` keeps what the step was about
    as plain values (e.g. the device's inventory number or the old return date),
    so the history stays readable when allocations or devices change later.
    """

    # Steps the employee sees in the portal; the rest is IT's internal work.
    EMPLOYEE_KINDS = (
        AssetRequestEventKind.CREATED,
        AssetRequestEventKind.DIRECT,
        AssetRequestEventKind.QUICK,
        AssetRequestEventKind.APPROVED,
        AssetRequestEventKind.DECLINED,
        AssetRequestEventKind.CONFIRMED,
        AssetRequestEventKind.REJECTED,
        AssetRequestEventKind.CANCELLED,
        AssetRequestEventKind.REPLACED,
        AssetRequestEventKind.READY,
        AssetRequestEventKind.RESCHEDULED,
        AssetRequestEventKind.HANDED_OUT,
        AssetRequestEventKind.RETURNED,
        AssetRequestEventKind.EXTENDED,
        AssetRequestEventKind.REMINDED,
        AssetRequestEventKind.COMPLETED,
    )

    # What a department approver sees: the request and the decision, not what IT does after.
    APPROVER_KINDS = (
        AssetRequestEventKind.CREATED,
        AssetRequestEventKind.APPROVED,
        AssetRequestEventKind.DECLINED,
    )

    asset_request = models.ForeignKey(
        "requests.AssetRequest",
        verbose_name=_("request"),
        on_delete=models.CASCADE,
        related_name="events",
    )
    kind = models.CharField(_("kind"), max_length=20, choices=AssetRequestEventKind.choices)
    at = models.DateTimeField(_("at"), default=timezone.now, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("by"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    data = models.JSONField(_("details"), default=dict, blank=True)

    class Meta:
        verbose_name = _("request event")
        verbose_name_plural = _("request events")
        ordering = ["at"]

    def __str__(self) -> str:
        return f"{self.asset_request_id} {self.kind} {self.at:%Y-%m-%d %H:%M}"
