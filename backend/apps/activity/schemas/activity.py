from datetime import datetime
from uuid import UUID

from apps.accounts.schemas import UserRefOut
from apps.activity.models import ActivityArea, ActivityKind
from apps.core.schemas.base import Schema


class ActivityOut(Schema):
    """One step of IT's work. ``subject_id`` is empty for a deleted object or several devices."""

    id: UUID
    occurred_at: datetime
    area: ActivityArea
    kind: ActivityKind
    subject_id: UUID | None
    subject_label: str
    actor: UserRefOut | None
    related_user: UserRefOut | None
    quantity: int | None
    detail: str
