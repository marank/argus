from datetime import datetime
from uuid import UUID

from ninja import Field, Schema

from apps.accounts.schemas import UserRefOut
from apps.inventory.models import AssetIssue
from apps.masterdata.schemas.refs import AssetModelRefOut


class IssueAssetOut(Schema):
    id: UUID
    inventory_number: str
    model: AssetModelRefOut
    assigned_to: UserRefOut | None


class AssetIssueOut(Schema):
    id: UUID
    asset: IssueAssetOut
    kind: str
    description: str
    status: str
    reported_by: UserRefOut | None
    handled_by: UserRefOut | None
    resolution: str
    resolved_at: datetime | None
    created_at: datetime


class OwnIssueOut(Schema):
    """What the employee sees of their own report."""

    id: UUID
    kind: str
    description: str
    status: str
    resolution: str
    created_at: datetime


class OwnIssueDeviceOut(Schema):
    id: UUID
    inventory_number: str
    model: AssetModelRefOut
    category_icon: str = Field(..., alias="model.category.icon")


class OwnIssueWithDeviceOut(OwnIssueOut):
    """An employee's report in their list of all reports."""

    asset: OwnIssueDeviceOut
    # The device may have been returned since; then there is no device page to open.
    still_assigned: bool


class AssetIssueIn(Schema):
    kind: AssetIssue.Kind = AssetIssue.Kind.DEFECT
    description: str = Field(..., max_length=2000)


class AssetIssueUpdateIn(Schema):
    status: AssetIssue.Status
    resolution: str = ""
