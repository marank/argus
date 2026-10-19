from uuid import UUID

from ninja import Schema


class RefOut(Schema):
    """Compact reference to a related record."""

    id: UUID
    name: str


class MessageOut(Schema):
    detail: str
