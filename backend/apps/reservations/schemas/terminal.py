from datetime import datetime
from uuid import UUID

from ninja import Field, Schema

from apps.core.schemas import RefOut
from apps.masterdata.schemas.refs import LocationRefOut

from .reservation import AllocationNoteIn


class TerminalPersonOut(Schema):
    id: UUID
    display_name: str
    employee_number: str
    department: RefOut | None


class TerminalPickupOut(Schema):
    """A prepared pickup as listed on the terminal (no IT-internal details)."""

    id: UUID
    number: str
    title: str
    requester: TerminalPersonOut
    pickup_at: datetime | None
    pickup_location: LocationRefOut | None
    unit_count: int = 0
    summary: str = ""

    @staticmethod
    def resolve_unit_count(obj) -> int:
        return sum(i.quantity_target for i in obj.items.all())

    @staticmethod
    def resolve_summary(obj) -> str:
        return ", ".join(f"{i.quantity_target}× {i.label}" for i in obj.items.all())


class TerminalSignIn(Schema):
    received_by: UUID | None = Field(None, description="Employee collecting the devices")
    received_by_name: str = Field("", max_length=150)
    signature: str = Field(..., description="PNG data URL of the signature")
    notes: str = ""
    allocation_notes: list[AllocationNoteIn] = []
