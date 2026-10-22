from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models.base import TimeStampedModel


class MailSettings(TimeStampedModel):
    """Outgoing mail via SMTP and which notifications are sent (one row)."""

    class Security(models.TextChoices):
        STARTTLS = "starttls", _("STARTTLS")
        SSL = "ssl", _("SSL/TLS")
        NONE = "none", _("None")

    enabled = models.BooleanField(_("send emails"), default=False)
    host = models.CharField(_("SMTP server"), max_length=255, blank=True)
    port = models.PositiveIntegerField(_("port"), default=587)
    security = models.CharField(
        _("encryption"), max_length=10, choices=Security.choices, default=Security.STARTTLS
    )
    username = models.CharField(_("user name"), max_length=255, blank=True)
    password = models.CharField(_("password"), max_length=255, blank=True)
    from_email = models.EmailField(_("sender address"), blank=True)
    from_name = models.CharField(_("sender name"), max_length=100, default="Argus")
    app_url = models.URLField(
        _("app address"),
        blank=True,
        help_text=_("Address of Argus for links in emails, e.g. https://argus.example.com"),
    )
    # Notification kinds switched off site-wide, per channel ({event: false}); see
    # ``apps.core.notifications.EVENTS``. ``events`` is email, ``app_events`` the bell.
    events = models.JSONField(_("email notifications"), default=dict, blank=True)
    app_events = models.JSONField(_("in-app notifications"), default=dict, blank=True)

    class Meta:
        verbose_name = _("mail settings")
        verbose_name_plural = _("mail settings")

    def __str__(self) -> str:
        return str(_("mail settings"))

    @classmethod
    def load(cls) -> MailSettings:
        obj = cls.objects.order_by("created_at").first()
        return obj or cls.objects.create()


class NotificationLog(TimeStampedModel):
    """One sent notification; the unique key keeps reminders from going out twice."""

    event = models.CharField(_("notification"), max_length=40)
    key = models.CharField(_("key"), max_length=200)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("recipient"),
        on_delete=models.CASCADE,
        related_name="+",
    )

    class Meta:
        verbose_name = _("sent notification")
        verbose_name_plural = _("sent notifications")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["event", "key", "recipient"], name="unique_notification"),
        ]
