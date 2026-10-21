from datetime import date
from string import Formatter

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import TimeStampedModel

PLACEHOLDERS = ("prefix", "year", "yy", "month", "seq")


def render_pattern(pattern: str, values: dict[str, str]) -> str:
    """Fills the placeholders of ``pattern``; anything beyond a bare known name is refused.

    Not ``str.format``: the pattern is user input, and format specs or attribute access
    (``{seq:>999999999}``, ``{prefix.__class__}``) would allocate memory or reach internals.
    """
    parts = []
    for literal, name, spec, conversion in Formatter().parse(pattern):
        parts.append(literal)
        if name is None:
            continue
        if name not in PLACEHOLDERS or spec or conversion:
            raise ValueError(f"{{{name}}}")
        parts.append(values[name])
    return "".join(parts)


class NumberSequence(TimeStampedModel):
    """Configurable number range, e.g. ``LT-2026-00042`` for laptops.

    The pattern supports the placeholders ``{prefix}``, ``{year}``, ``{yy}``,
    ``{month}`` and ``{seq}``. ``{seq}`` is zero-padded to ``padding`` digits.
    """

    class ResetPeriod(models.TextChoices):
        NEVER = "never", _("Never")
        YEARLY = "yearly", _("Yearly")
        MONTHLY = "monthly", _("Monthly")

    code = models.SlugField(_("code"), max_length=50, blank=True)
    name = models.CharField(_("name"), max_length=100)
    prefix = models.CharField(_("prefix"), max_length=20, blank=True)
    pattern = models.CharField(_("pattern"), max_length=100, default="{prefix}{seq}")
    padding = models.PositiveSmallIntegerField(_("padding"), default=5)
    next_value = models.PositiveIntegerField(_("next value"), default=1)
    reset_period = models.CharField(
        _("reset period"), max_length=10, choices=ResetPeriod.choices, default=ResetPeriod.NEVER
    )
    period_key = models.CharField(_("current period"), max_length=10, blank=True, editable=False)
    # Argus draws inventory, reservation and order numbers from these by code
    # (apps.core.services.numbering); their code stays fixed and they cannot be deleted.
    is_system = models.BooleanField(_("system sequence"), default=False, editable=False)

    class Meta:
        verbose_name = _("number sequence")
        verbose_name_plural = _("number sequences")
        ordering = ["name"]
        constraints = [
            # The code is optional; given codes stay unique.
            models.UniqueConstraint(
                fields=["code"],
                condition=~models.Q(code=""),
                name="unique_number_sequence_code",
                violation_error_message=_("A number sequence with this code already exists."),
                # Reported at the code field rather than for the whole form.
                violation_error_code="unique",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.preview()})"

    def clean(self) -> None:
        if self.is_system and not self._state.adding:
            saved = NumberSequence.objects.filter(pk=self.pk).values_list("code", flat=True).first()
            if self.code != saved:
                raise ValidationError(
                    {"code": _("Argus draws numbers from this sequence by its code; it cannot be changed.")}
                )
        if "{seq}" not in self.pattern:
            raise ValidationError({"pattern": _("The pattern must contain the {seq} placeholder.")})
        try:
            self.format(1)
        except ValueError as exc:
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
        return render_pattern(
            self.pattern,
            {
                "prefix": self.prefix,
                "year": str(on.year),
                "yy": f"{on.year % 100:02d}",
                "month": f"{on.month:02d}",
                "seq": str(value).zfill(self.padding),
            },
        )

    def preview(self) -> str:
        value = 1 if self.period_key != self.current_period_key() else self.next_value
        return self.format(value)
