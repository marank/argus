from decimal import Decimal
from uuid import UUID

from ninja import Field, Schema

from apps.accounts.schemas import TeamRefOut, default_team
from apps.core.api.security import context_is_it_staff
from apps.core.schemas import RefOut, per_response
from apps.core.services.numbering import get_sequence
from apps.masterdata.models import AssetModel

from .refs import AssetModelRefOut, CategoryRefOut


class AssetModelOut(Schema):
    id: UUID
    name: str
    designation: str
    full_name: str
    manufacturer: RefOut
    category: CategoryRefOut
    part_number: str
    ean: str
    tracking: str
    description: str
    specifications: str
    default_supplier: RefOut | None
    list_price: Decimal | None
    warranty_months: int
    compatible_with: list[AssetModelRefOut]
    number_sequence: RefOut | None
    # The sequence new devices draw from: the model's own, the category's or the general one.
    # Empty for consumables and licenses, which get no inventory numbers.
    effective_number_sequence: RefOut | None = None
    is_requestable: bool
    is_active: bool
    # IT-internal: empty for employees.
    team: TeamRefOut | None = None
    # The team that applies: the own, the category's (or a parent's) or the default team; IT-internal.
    effective_team: TeamRefOut | None = None

    @staticmethod
    def resolve_team(obj, context):
        return obj.team if context_is_it_staff(context) else None

    @staticmethod
    def resolve_effective_team(obj: AssetModel, context):
        if not context_is_it_staff(context):
            return None
        return obj.effective_team() or default_team(context)

    @staticmethod
    def resolve_effective_number_sequence(obj: AssetModel, context):
        if obj.tracking != AssetModel.Tracking.SERIALIZED:
            return None
        return obj.effective_number_sequence() or per_response(
            context, "general_asset_sequence", lambda: get_sequence("asset")
        )

    @staticmethod
    def resolve_compatible_with(obj: AssetModel):
        return list(obj.compatible_with.select_related("manufacturer"))


class AssetModelIn(Schema):
    name: str
    designation: str
    manufacturer: UUID
    category: UUID
    part_number: str = ""
    ean: str = ""
    tracking: AssetModel.Tracking = AssetModel.Tracking.SERIALIZED
    description: str = ""
    specifications: str = ""
    default_supplier: UUID | None = None
    list_price: Decimal | None = None
    warranty_months: int = Field(24, ge=0)
    compatible_with: list[UUID] = []
    number_sequence: UUID | None = None
    is_requestable: bool = True
    is_active: bool = True
    team: UUID | None = None
