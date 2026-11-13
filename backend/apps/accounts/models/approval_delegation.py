from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class ApprovalDelegation(TimeStampedModel):
    """An approver hands their approvals to a delegate for a period, e.g. a holiday.

    While the period runs the delegate may decide everything the approver may decide and
    is notified like the approver; the approver keeps deciding as well. Approvers manage
    their delegations themselves on the delegation page.
    """

    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("approver"),
        on_delete=models.CASCADE,
        related_name="delegations",
    )
    delegate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("delegate"),
        on_delete=models.CASCADE,
        related_name="received_delegations",
    )
    starts_on = models.DateField(_("from"))
    ends_on = models.DateField(_("until"), null=True, blank=True, help_text=_("Empty: until removed."))

    class Meta:
        verbose_name = _("approval delegation")
        verbose_name_plural = _("approval delegations")
        ordering = ["starts_on", "created_at"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(approver=F("delegate")),
                name="delegate_is_not_the_approver",
                violation_error_message=_("You cannot delegate to yourself."),
            ),
            models.CheckConstraint(
                condition=Q(ends_on__isnull=True) | Q(ends_on__gte=F("starts_on")),
                name="delegation_period_in_order",
                violation_error_message=_("The end must not be before the start."),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.delegate} → {self.approver}"
