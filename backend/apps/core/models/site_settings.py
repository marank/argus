from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models.base import TimeStampedModel


class SiteSettings(TimeStampedModel):
    """Site-wide switches and rules (one row); modules and features see ``apps.core.features``."""

    flags = models.JSONField(_("modules and features"), default=dict, blank=True)

    # Deadlines and warning periods.
    warranty_warning_days = models.PositiveSmallIntegerField(
        _("warranty warning (days)"),
        default=60,
        help_text=_("Warranties ending within this many days count as ending soon."),
    )
    license_warning_days = models.PositiveSmallIntegerField(
        _("license warning (days)"),
        default=60,
        help_text=_("Licenses ending within this many days count as ending soon."),
    )
    default_loan_days = models.PositiveSmallIntegerField(
        _("default loan period (days)"),
        default=5,
        help_text=_("Suggested length of a temporary request."),
    )
    max_loan_days = models.PositiveSmallIntegerField(
        _("maximum loan period (days)"),
        default=0,
        help_text=_("Longest allowed temporary request; 0 = no limit."),
    )
    return_reminder_days = models.PositiveSmallIntegerField(
        _("return reminder (days before)"),
        default=2,
        help_text=_("Employees are reminded this many days before a return is due."),
    )

    # Sign-in.
    session_hours = models.PositiveSmallIntegerField(
        _("session duration (hours)"),
        default=12,
        help_text=_("How long a sign-in lasts; a user's own value overrides it."),
    )

    class Meta:
        verbose_name = _("site settings")
        verbose_name_plural = _("site settings")

    def __str__(self) -> str:
        return str(_("site settings"))

    @classmethod
    def load(cls) -> SiteSettings:
        """The single settings row, created with defaults on first access."""
        obj = cls.objects.order_by("created_at").first()
        return obj or cls.objects.create()


RULE_FIELDS = (
    "warranty_warning_days",
    "license_warning_days",
    "default_loan_days",
    "max_loan_days",
    "return_reminder_days",
    "session_hours",
)
