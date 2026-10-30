from uuid import UUID

from ninja import Schema


class ManufacturerOut(Schema):
    id: UUID
    name: str
    website: str
    support_url: str
    support_phone: str
    notes: str
    is_active: bool


class ManufacturerIn(Schema):
    name: str
    website: str = ""
    support_url: str = ""
    support_phone: str = ""
    notes: str = ""
    is_active: bool = True
