"""Reading in-app notifications (the bell): the change reaches the user's other tabs too."""

from typing import TYPE_CHECKING
from uuid import UUID

from django.utils import timezone

from apps.core.live import publish
from apps.core.models import Notification

if TYPE_CHECKING:
    from apps.accounts.models import User


def _changed(user_id: UUID) -> None:
    """Other tabs of the user update their bell too."""
    publish("notification", None, users=[user_id], staff=False)


def mark_read(notification: Notification) -> Notification:
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at", "updated_at"])
        _changed(notification.recipient_id)
    return notification


def mark_all_read(user: User) -> None:
    now = timezone.now()
    Notification.objects.filter(recipient=user, read_at__isnull=True).update(read_at=now, updated_at=now)
    _changed(user.pk)
