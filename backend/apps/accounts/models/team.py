from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Team(TimeStampedModel):
    """A group of IT staff that requests can be assigned to, e.g. "IT support" or "Ledgerline".

    Unlike departments (where employees work), a team is an IT work queue and one
    person may belong to several. With an LDAP group the members follow the
    directory: they are added or removed when they sign in.
    """

    name = models.CharField(_("name"), max_length=100, unique=True)
    code = models.CharField(_("code"), max_length=20, blank=True)
    sort_order = models.PositiveIntegerField(
        _("sort order"), default=0, help_text=_("Lower numbers come first; equal numbers by name.")
    )
    ldap_group_dn = models.CharField(
        _("LDAP group"),
        max_length=500,
        blank=True,
        help_text=_("DN of a directory group; its members join the team when they sign in."),
    )
    is_default = models.BooleanField(
        _("default team"),
        default=False,
        help_text=_("Gets new requests and reports that no category or model routes elsewhere."),
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, verbose_name=_("members"), blank=True, related_name="teams"
    )

    class Meta:
        verbose_name = _("team")
        verbose_name_plural = _("teams")
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        # Only one default team: choosing a new one takes the mark from the old one.
        # (No unique constraint: form validation would refuse the switch before this runs.)
        if self.is_default:
            Team.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
