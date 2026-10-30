from uuid import UUID

from ninja import Field

from apps.core.models import NumberSequence
from apps.core.schemas.base import Schema


class NumberSequenceOut(Schema):
    id: UUID
    code: str
    name: str
    prefix: str
    pattern: str
    padding: int
    next_value: int
    reset_period: NumberSequence.ResetPeriod
    is_system: bool
    preview: str

    @staticmethod
    def resolve_preview(obj: NumberSequence) -> str:
        return obj.preview()


class NumberSequenceIn(Schema):
    name: str
    code: str = ""
    prefix: str = ""
    pattern: str = "{prefix}{seq}"
    padding: int = Field(5, ge=1, le=12)
    next_value: int = Field(1, ge=1)
    reset_period: NumberSequence.ResetPeriod = NumberSequence.ResetPeriod.NEVER
