from datetime import date, datetime
from typing import Any

from ninja import Schema


class CalendarEntryOut(Schema):
    id: str
    kind: str
    title: str
    start: datetime | date
    end: date | None
    all_day: bool
    status: str
    overdue: bool
    due: date | None
    # Untyped values keep the published schema a free-form object.
    link: dict[str, Any]
    details: list[str]
