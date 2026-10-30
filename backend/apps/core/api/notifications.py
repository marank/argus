"""The signed-in user's in-app notifications (the bell)."""

from datetime import datetime
from uuid import UUID

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import Router, Schema
from ninja.pagination import paginate

from apps.core.api.pagination import Pagination
from apps.core.api.security import AuthedRequest
from apps.core.live import publish
from apps.core.models import Notification

router = Router(tags=["notifications"])


class NotificationOut(Schema):
    id: UUID
    event: str
    title: str
    text: str
    path: str
    read_at: datetime | None
    created_at: datetime


class UnreadOut(Schema):
    unread: int


def _changed(request: AuthedRequest) -> None:
    """Other tabs of the user update their bell too."""
    publish("notification", None, users=[request.user.pk], staff=False)


@router.get("", response=list[NotificationOut])
@paginate(Pagination)
def list_notifications(request: AuthedRequest, unread: bool = False) -> QuerySet[Notification]:
    queryset = Notification.objects.filter(recipient=request.user)
    return queryset.filter(read_at__isnull=True) if unread else queryset


@router.get("/unread", response=UnreadOut)
def unread_count(request: AuthedRequest) -> dict[str, int]:
    return {"unread": Notification.objects.filter(recipient=request.user, read_at__isnull=True).count()}


@router.post("/{uuid:pk}/read", response=NotificationOut)
def mark_read(request: AuthedRequest, pk: UUID) -> Notification:
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at", "updated_at"])
        _changed(request)
    return notification


@router.post("/read-all", response=UnreadOut)
def mark_all_read(request: AuthedRequest) -> dict[str, int]:
    Notification.objects.filter(recipient=request.user, read_at__isnull=True).update(
        read_at=timezone.now(), updated_at=timezone.now()
    )
    _changed(request)
    return {"unread": 0}
