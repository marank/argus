from uuid import UUID

from ninja import Schema

from apps.masterdata.schemas.refs import AssetModelRefOut


class AssetRefOut(Schema):
    id: UUID
    inventory_number: str
    serial_number: str
    status: str
    model: AssetModelRefOut
