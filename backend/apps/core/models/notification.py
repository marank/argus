from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models.base import TimeStampedModel


class Notification(TimeStampedModel):
    """A notification shown in the app (the bell), next to or instead of the email.

    Title and text are rendered in the recipient's language when it is created, like
    the email; ``path`` is the page it is about. ``key`` keeps reminders from showing
    twice, as ``NotificationLog`` does for emails.
    """

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("recipient"),
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    event = models.CharField(_("notification"), max_length=40)
    key = models.CharField(_("key"), max_length=200, blank=True)
    title = models.CharField(_("title"), max_length=255)
    text = models.TextField(_("text"), blank=True)
    path = models.CharField(_("link"), max_length=300, blank=True)
    read_at = models.DateTimeField(_("read at"), null=True, blank=True)

    class Meta:
        verbose_name = _("in-app notification")
        verbose_name_plural = _("in-app notifications")
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "read_at"], name="notification_unread")]

    def __str__(self) -> str:
        return self.title
