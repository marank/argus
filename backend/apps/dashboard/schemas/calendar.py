from datetime import date, datetime

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
    link: dict
    details: list[str]
