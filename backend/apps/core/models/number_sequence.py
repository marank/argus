from datetime import date

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import TimeStampedModel

PLACEHOLDERS = ("prefix", "year", "yy", "month", "seq")


class NumberSequence(TimeStampedModel):
    """Configurable number range, e.g. ``LT-2026-00042`` for laptops.

    The pattern supports the placeholders ``{prefix}``, ``{year}``, ``{yy}``,
    ``{month}`` and ``{seq}``. ``{seq}`` is zero-padded to ``padding`` digits.
    """

    class ResetPeriod(models.TextChoices):
        NEVER = "never", _("Never")
        YEARLY = "yearly", _("Yearly")
        MONTHLY = "monthly", _("Monthly")

    code = models.SlugField(_("code"), max_length=50, unique=True)
    name = models.CharField(_("name"), max_length=100)
    prefix = models.CharField(_("prefix"), max_length=20, blank=True)
    pattern = models.CharField(_("pattern"), max_length=100, default="{prefix}{seq}")
    padding = models.PositiveSmallIntegerField(_("padding"), default=5)
    next_value = models.PositiveIntegerField(_("next value"), default=1)
    reset_period = models.CharField(
        _("reset period"), max_length=10, choices=ResetPeriod.choices, default=ResetPeriod.NEVER
    )
    period_key = models.CharField(_("current period"), max_length=10, blank=True, editable=False)

    class Meta:
        verbose_name = _("number sequence")
        verbose_name_plural = _("number sequences")
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.preview()})"

    def clean(self) -> None:
        if "{seq}" not in self.pattern:
            raise ValidationError({"pattern": _("The pattern must contain the {seq} placeholder.")})
        try:
            self.format(1)
        except (KeyError, IndexError, ValueError) as exc:
            raise ValidationError({"pattern": _("Invalid placeholder: %(error)s") % {"error": exc}}) from exc

    def current_period_key(self, on: date | None = None) -> str:
        on = on or date.today()
        match self.reset_period:
            case self.ResetPeriod.YEARLY:
                return f"{on.year}"
            case self.ResetPeriod.MONTHLY:
                return f"{on.year}-{on.month:02d}"
            case _:
                return ""

    def format(self, value: int, on: date | None = None) -> str:
        on = on or date.today()
        return self.pattern.format(
            prefix=self.prefix,
            year=on.year,
            yy=f"{on.year % 100:02d}",
            month=f"{on.month:02d}",
            seq=str(value).zfill(self.padding),
        )

    def preview(self) -> str:
        value = 1 if self.period_key != self.current_period_key() else self.next_value
        return self.format(value)
