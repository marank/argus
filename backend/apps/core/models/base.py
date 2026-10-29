import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class UUIDModel(models.Model):
    """Abstract base with a UUID primary key (also used in URLs).

    UUIDv7: random, but in creation order, which keeps the primary key indexes compact.
    Lists still order explicitly; the ID only breaks ties.
    """

    id = models.UUIDField(_("ID"), primary_key=True, default=uuid.uuid7, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(UUIDModel):
    """Abstract base adding creation and modification timestamps."""

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        abstract = True
