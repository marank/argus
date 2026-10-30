from uuid import UUID

from ninja import Schema


class SupplierOut(Schema):
    id: UUID
    name: str
    customer_number: str
    contact_person: str
    email: str
    phone: str
    website: str
    address: str
    notes: str
    is_active: bool


class SupplierIn(Schema):
    name: str
    customer_number: str = ""
    contact_person: str = ""
    email: str = ""
    phone: str = ""
    website: str = ""
    address: str = ""
    notes: str = ""
    is_active: bool = True
