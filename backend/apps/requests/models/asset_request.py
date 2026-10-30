from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from apps.accounts.models import User


class AssetRequestStatus(models.TextChoices):
    PENDING_APPROVAL = "pending_approval", _("Awaiting approval")
    SUBMITTED = "submitted", _("Submitted")
    CONFIRMED = "confirmed", _("Confirmed")
    READY = "ready", _("Ready for pickup")
    HANDED_OUT = "handed_out", _("Handed out")
    COMPLETED = "completed", _("Completed")
    REJECTED = "rejected", _("Rejected")
    CANCELLED = "cancelled", _("Cancelled")


class AssetRequest(TimeStampedModel):
    """An employee's request for devices, either for a period or permanently.

    Life cycle::

        (pending_approval ─►) submitted ─► confirmed ─► ready ─► handed_out ─► completed
                 │                │            │          (permanent requests complete on hand-out)
                 └────────────────┴────────────┴─► rejected / cancelled

    Requests for categories that need approval wait for an approver of the
    requester's department first (``pending_approval``); IT only gets them once
    approved. Requests without anything to collect (only software) are handed
    out right when they are marked ready. Temporary requests stay handed out
    until the devices and license seats are back; consumables are not returned.

    Direct hand-outs (``origin``) are recorded by IT for devices handed out on the
    spot: they skip straight to handed out.
    """

    class Duration(models.TextChoices):
        TEMPORARY = "temporary", _("Temporary")
        PERMANENT = "permanent", _("Permanent")

    class HandoverMode(models.TextChoices):
        PICKUP = "pickup", _("Pickup with signature")
        # The employee collects at the IT desk; IT records afterwards who received the devices.
        COLLECT = "collect", _("Simple pickup")
        DELIVERY = "delivery", _("Delivered by IT")

    class Approval(models.TextChoices):
        """The department's decision; empty when the request did not need one."""

        NOT_REQUIRED = "", _("Not required")
        PENDING = "pending", _("Pending")
        APPROVED = "approved", _("Approved")
        REJECTED = "rejected", _("Rejected")

    class Origin(models.TextChoices):
        REQUEST = "request", _("Request")
        # IT handed out devices on the spot; the request only documents it.
        DIRECT = "direct", _("Direct hand-out")
        # IT assigned a device from its page in one step: recorded as handed out right away.
        QUICK = "quick", _("Quick assignment")

    OPEN_STATUSES = (
        AssetRequestStatus.PENDING_APPROVAL,
        AssetRequestStatus.SUBMITTED,
        AssetRequestStatus.CONFIRMED,
        AssetRequestStatus.READY,
        AssetRequestStatus.HANDED_OUT,
    )
    CANCELLABLE_STATUSES = (
        AssetRequestStatus.PENDING_APPROVAL,
        AssetRequestStatus.SUBMITTED,
        AssetRequestStatus.CONFIRMED,
        AssetRequestStatus.READY,
    )
    # The hand-out is still ahead: a date IT plans for, confirmed or not.
    AWAITING_HANDOUT_STATUSES = CANCELLABLE_STATUSES
    # Devices handed out permanently can still be taken back later.
    RETURNABLE_STATUSES = (AssetRequestStatus.HANDED_OUT, AssetRequestStatus.COMPLETED)

    number = models.CharField(_("number"), max_length=30, unique=True, blank=True)
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("requester"),
        on_delete=models.PROTECT,
        related_name="asset_requests",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("created by"),
        on_delete=models.SET_NULL,
        null=True,
        related_name="+",
    )
    title = models.CharField(_("purpose"), max_length=200)
    notes = models.TextField(_("notes"), blank=True)
    duration = models.CharField(
        _("duration"), max_length=10, choices=Duration.choices, default=Duration.TEMPORARY
    )
    start_date = models.DateField(_("needed from"))
    # The employee's wish; IT sets the actual appointment in ``pickup_at``.
    requested_pickup_date = models.DateField(_("preferred pickup day"), null=True, blank=True)
    end_date = models.DateField(_("needed until"), null=True, blank=True)
    origin = models.CharField(_("origin"), max_length=10, choices=Origin.choices, default=Origin.REQUEST)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=AssetRequestStatus.choices,
        default=AssetRequestStatus.SUBMITTED,
        db_index=True,
    )
    approval = models.CharField(
        _("approval"), max_length=10, choices=Approval.choices, default=Approval.NOT_REQUIRED, blank=True
    )
    # Who decided for the department; the requester when they approve for it themselves.
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("approver"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    approval_decided_at = models.DateTimeField(_("approval decided at"), null=True, blank=True)
    approval_comment = models.TextField(_("approval comment"), blank=True)

    pickup_at = models.DateTimeField(_("pickup at"), null=True, blank=True)
    pickup_location = models.ForeignKey(
        "masterdata.Location",
        verbose_name=_("pickup location"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    handover_mode = models.CharField(
        _("handover"),
        max_length=10,
        choices=HandoverMode.choices,
        default=HandoverMode.PICKUP,
        help_text=_("Pickup requests appear on the pickup terminal once they are ready."),
    )
    skip_device_check = models.BooleanField(
        _("skip device check"),
        default=False,
        help_text=_("The pickup terminal starts with who collects, without checking the devices."),
    )
    it_comment = models.TextField(_("IT comment"), blank=True)
    # Asked again after an earlier request was declined or closed; shown to the approver.
    follows = models.ForeignKey(
        "self",
        verbose_name=_("follows"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("handled by"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="handled_asset_requests",
    )
    # Who is responsible, set on purpose by IT (``handled_by`` is just the last one acting).
    # Both are optional and independent: a team, a person, both or neither.
    assigned_team = models.ForeignKey(
        "accounts.Team",
        verbose_name=_("team"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asset_requests",
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("assignee"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_asset_requests",
    )
    prepared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("prepared by"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text=_("Who marked the request ready; shown as handing out at the pickup terminal."),
    )
    reminded_at = models.DateTimeField(
        _("reminded at"),
        null=True,
        blank=True,
        help_text=_("When IT last reminded the employee to return the devices."),
    )
    reminded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("reminded by"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    confirmed_at = models.DateTimeField(_("confirmed at"), null=True, blank=True)
    handed_out_at = models.DateTimeField(_("handed out at"), null=True, blank=True)
    completed_at = models.DateTimeField(_("completed at"), null=True, blank=True)

    # Cached by ``schemas.asset_request.pending_approvers``, not a column.
    _pending_approvers: list[User]

    class Meta:
        verbose_name = _("request")
        verbose_name_plural = _("requests")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.number} – {self.title}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.number:
            from apps.core.services.numbering import next_number

            self.number = next_number(
                "request", taken=lambda n: AssetRequest.objects.filter(number=n).exists()
            )
        super().save(*args, **kwargs)

    def approvers(self) -> QuerySet[User]:
        """Who may approve for the requester's department, or for the nearest one above it
        that has approvers (none without a department)."""
        from apps.accounts.models import User

        department = self.requester.department
        source = department.approval_source() if department else None
        if source is None:
            return User.objects.none()
        return User.objects.filter(approving_departments=source, is_active=True)

    def may_approve(self, user: User) -> bool:
        return self.approvers().filter(pk=user.pk).exists()

    @property
    def is_overdue(self) -> bool:
        return (
            self.status == AssetRequestStatus.HANDED_OUT
            and self.end_date is not None
            and self.end_date < timezone.localdate()
        )
