from typing import Any

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.permissions import clean_permissions
from apps.core.models import TimeStampedModel


class Role(TimeStampedModel):
    """A set of rights for IT staff, e.g. "Support" or "Purchasing".

    ``permissions`` maps an area of the app to "read" or "write"; areas left
    out are not accessible. Staff can hold several roles; their rights add up.
    """

    name = models.CharField(_("name"), max_length=100, unique=True)
    description = models.TextField(_("description"), blank=True)
    permissions = models.JSONField(_("permissions"), default=dict, blank=True)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, verbose_name=_("members"), blank=True, related_name="roles"
    )

    class Meta:
        verbose_name = _("role")
        verbose_name_plural = _("roles")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.permissions = clean_permissions(self.permissions)
        super().save(*args, **kwargs)
