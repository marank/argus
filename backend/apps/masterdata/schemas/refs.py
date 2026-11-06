from uuid import UUID

from apps.core.schemas.base import Schema
from apps.masterdata.models import AssetModel, CategoryKind


class AssetModelRefOut(Schema):
    id: UUID
    name: str
    designation: str
    full_name: str
    tracking: AssetModel.Tracking


class LocationRefOut(Schema):
    id: UUID
    name: str
    full_name: str


class CategoryRefOut(Schema):
    id: UUID
    name: str
    kind: CategoryKind
    item_name: str
    code: str
    icon: str
    identifier_label: str
