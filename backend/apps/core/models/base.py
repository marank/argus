import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class UUIDModel(models.Model):
    """Abstract base using a random UUID as primary key (also used in URLs)."""

    id = models.UUIDField(_("ID"), primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(UUIDModel):
    """Abstract base adding creation and modification timestamps."""

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        abstract = True
