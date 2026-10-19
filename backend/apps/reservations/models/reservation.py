from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Reservation(TimeStampedModel):
    """An employee's request for devices, either for a period or permanently.

    Life cycle::

        submitted ─► approved ─► ready ─► handed_out ─► completed
            │            │                     (permanent requests complete on hand-out)
            └─► rejected / cancelled
    """

    class Status(models.TextChoices):
        SUBMITTED = "submitted", _("Submitted")
        APPROVED = "approved", _("Approved")
        READY = "ready", _("Ready for pickup")
        HANDED_OUT = "handed_out", _("Handed out")
        COMPLETED = "completed", _("Completed")
        REJECTED = "rejected", _("Rejected")
        CANCELLED = "cancelled", _("Cancelled")

    class Duration(models.TextChoices):
        TEMPORARY = "temporary", _("Temporary")
        PERMANENT = "permanent", _("Permanent")

    class HandoverMode(models.TextChoices):
        PICKUP = "pickup", _("Pickup with signature")
        DELIVERY = "delivery", _("Delivered by IT")

    OPEN_STATUSES = (Status.SUBMITTED, Status.APPROVED, Status.READY, Status.HANDED_OUT)
    CANCELLABLE_STATUSES = (Status.SUBMITTED, Status.APPROVED, Status.READY)

    number = models.CharField(_("number"), max_length=30, unique=True, blank=True)
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("requester"),
        on_delete=models.PROTECT,
        related_name="reservations",
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
    end_date = models.DateField(_("needed until"), null=True, blank=True)
    status = models.CharField(
        _("status"), max_length=12, choices=Status.choices, default=Status.SUBMITTED, db_index=True
    )

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
    it_comment = models.TextField(_("IT comment"), blank=True)
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("handled by"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="handled_reservations",
    )
    approved_at = models.DateTimeField(_("approved at"), null=True, blank=True)
    handed_out_at = models.DateTimeField(_("handed out at"), null=True, blank=True)
    completed_at = models.DateTimeField(_("completed at"), null=True, blank=True)

    class Meta:
        verbose_name = _("reservation")
        verbose_name_plural = _("reservations")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.number} – {self.title}"

    def save(self, *args, **kwargs):
        if not self.number:
            from apps.core.services.numbering import next_number

            self.number = next_number("reservation")
        super().save(*args, **kwargs)

    @property
    def is_overdue(self) -> bool:
        return (
            self.status == self.Status.HANDED_OUT
            and self.end_date is not None
            and self.end_date < timezone.localdate()
        )
