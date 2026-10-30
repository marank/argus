from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models.base import TimeStampedModel, UUIDModel


class TwoFactorMethod(models.TextChoices):
    EMAIL = "email", _("Code by email")
    TOTP = "totp", _("Authenticator app")


class TwoFactor(TimeStampedModel):
    """The second sign-in step a user switched on; see ``apps.accounts.services.two_factor``."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name=_("user"),
        on_delete=models.CASCADE,
        related_name="two_factor",
    )
    method = models.CharField(_("method"), max_length=10, choices=TwoFactorMethod.choices)
    # Base32 secret of the authenticator app (TOTP method only).
    totp_secret = models.CharField(_("app secret"), max_length=64, blank=True, editable=False)
    # Time step of the last accepted app code: a code cannot be used twice.
    totp_last_step = models.BigIntegerField(default=0, editable=False)

    class Meta:
        verbose_name = _("two-factor sign-in")
        verbose_name_plural = _("two-factor sign-ins")

    def __str__(self) -> str:
        return f"{self.user} · {self.get_method_display()}"


class BackupCode(UUIDModel):
    """One-time code for signing in without the second factor; only a salted hash is stored."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("user"),
        on_delete=models.CASCADE,
        related_name="backup_codes",
    )
    salt = models.CharField(max_length=32, editable=False)
    code_hash = models.CharField(max_length=64, editable=False)
    used_at = models.DateTimeField(_("used at"), null=True, blank=True, editable=False)

    class Meta:
        verbose_name = _("backup code")
        verbose_name_plural = _("backup codes")
