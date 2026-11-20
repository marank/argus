"""The signed-in user's in-app notifications (the bell)."""

from datetime import datetime
from uuid import UUID

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.pagination import paginate

from apps.core.api.pagination import Pagination
from apps.core.api.security import AuthedRequest
from apps.core.models import Notification
from apps.core.schemas.base import Schema
from apps.core.services import notifications

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
    return notifications.mark_read(notification)


@router.post("/read-all", response=UnreadOut)
def mark_all_read(request: AuthedRequest) -> dict[str, int]:
    notifications.mark_all_read(request.user)
    return {"unread": 0}
