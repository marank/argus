from uuid import UUID

from apps.core.schemas.base import Schema
from apps.inventory.models import AssetStatus
from apps.masterdata.schemas.refs import AssetModelRefOut


class AssetRefOut(Schema):
    id: UUID
    inventory_number: str
    name: str
    serial_number: str
    status: AssetStatus
    model: AssetModelRefOut
