from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import UUIDModel


class HandoverMethod(models.TextChoices):
    SIGNATURE = "signature", _("Signed at pickup terminal")
    DELIVERED = "delivered", _("Delivered by IT")
    DIRECT = "direct", _("Handed out by IT")


class Handover(UUIDModel):
    """Record of how the devices of a request reached the employee.

    ``SIGNATURE`` hand-outs happen at the pickup terminal: the person collecting
    the devices is recorded and signs on screen. ``DELIVERED`` and ``DIRECT``
    hand-outs are documented by the IT staff member without a signature.
    """

    asset_request = models.OneToOneField(
        "requests.AssetRequest",
        verbose_name=_("request"),
        on_delete=models.CASCADE,
        related_name="handover",
    )
    method = models.CharField(_("method"), max_length=10, choices=HandoverMethod.choices)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("received by"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_handovers",
    )
    received_by_name = models.CharField(
        _("received by (name)"),
        max_length=150,
        help_text=_("Kept as text so the record stays readable if the account is removed."),
    )
    signature = models.TextField(_("signature"), blank=True, help_text=_("PNG image as data URL."))
    notes = models.TextField(_("notes"), blank=True)
    location = models.CharField(_("delivered to"), max_length=150, blank=True)
    # The IT staff member responsible for the hand-out; at the terminal the one who
    # prepared the pickup unless the terminal names someone else.
    handed_out_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("handed out by"),
        on_delete=models.SET_NULL,
        null=True,
        related_name="+",
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("recorded by"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text=_("The account the hand-out was recorded with, e.g. the pickup terminal."),
    )
    handed_out_at = models.DateTimeField(_("handed out at"), auto_now_add=True)

    class Meta:
        verbose_name = _("handover")
        verbose_name_plural = _("handovers")

    def __str__(self) -> str:
        return f"{self.asset_request.number} → {self.received_by_name}"
