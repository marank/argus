from uuid import UUID

from ninja import Schema


class AssetModelRefOut(Schema):
    id: UUID
    name: str
    designation: str
    full_name: str
    tracking: str


class LocationRefOut(Schema):
    id: UUID
    name: str
    full_name: str


class CategoryRefOut(Schema):
    id: UUID
    name: str
    kind: str
    item_name: str
    code: str
    icon: str
