from datetime import date, datetime
from typing import Literal

from ninja import Schema


class CalendarEntryOut(Schema):
    id: str
    kind: Literal["loan", "pickup", "return", "delivery", "warranty", "license"]
    title: str
    start: datetime | date
    end: date | None
    all_day: bool
    status: str
    overdue: bool
    due: date | None
    # Route name plus ``id``, or ``warranty_until`` for the devices whose warranty ends.
    link: dict[str, str]
    details: list[str]
