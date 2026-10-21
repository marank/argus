from datetime import date, datetime
from uuid import UUID

from ninja import Field, Schema

from apps.accounts.schemas import TeamRefOut, UserRefOut
from apps.core.api.security import context_is_it_staff
from apps.inventory.models import AssetIssue, AssetIssueEntry
from apps.masterdata.schemas.refs import AssetModelRefOut, LocationRefOut


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
    assigned_team: TeamRefOut | None
    assignee: UserRefOut | None
    resolved_at: datetime | None
    created_at: datetime


class OwnIssueOut(Schema):
    """What the employee sees of their own report."""

    id: UUID
    kind: str
    description: str
    status: str
    created_at: datetime
    # IT wrote or changed the status since the employee last looked.
    unseen_update: bool
    last_message: str | None

    @staticmethod
    def resolve_last_message(obj: AssetIssue) -> str | None:
        """The latest message of either side; few reports per employee, so a query each is fine."""
        entry = obj.entries.filter(kind=AssetIssueEntry.Kind.MESSAGE).order_by("created_at").last()
        return entry.text if entry else None


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


class AssignIn(Schema):
    team: UUID | None = None
    assignee: UUID | None = None


class AssetIssueUpdateIn(Schema):
    status: AssetIssue.Status
    # Sent along with the change, e.g. what was done.
    message: str = Field("", max_length=4000)


class IssueMessageIn(Schema):
    # Optional when sent along with marking a report resolved.
    text: str = Field("", max_length=4000)


class IssueEntryOut(Schema):
    id: UUID
    kind: str
    author: UserRefOut | None
    # "reporter" or "it": which side it came from.
    side: str
    text: str
    status: str
    created_at: datetime


class IssueReporterOut(Schema):
    id: UUID
    display_name: str
    email: str
    phone: str
    job_title: str
    department: str | None = Field(None, alias="department.name")


def _shows_holder(asset, context) -> bool:
    """IT sees who has a device; the reporter only themselves (not who got it since)."""
    if context_is_it_staff(context):
        return True
    request = (context or {}).get("request")
    return (
        request is not None and asset.assigned_to_id is not None and asset.assigned_to_id == request.user.pk
    )


class IssueDeviceDetailOut(Schema):
    id: UUID
    inventory_number: str
    serial_number: str
    hostname: str
    status: str
    model: AssetModelRefOut
    category: str = Field(..., alias="model.category.name")
    category_icon: str = Field(..., alias="model.category.icon")
    assigned_to: UserRefOut | None
    assigned_since: datetime | None
    location: LocationRefOut | None
    purchase_date: date | None
    warranty_until: date | None

    @staticmethod
    def resolve_assigned_to(obj, context):
        return obj.assigned_to if _shows_holder(obj, context) else None

    @staticmethod
    def resolve_assigned_since(obj, context):
        return obj.assigned_since if _shows_holder(obj, context) else None


class IssueSummaryOut(Schema):
    """Another report on the same device."""

    id: UUID
    kind: str
    description: str
    status: str
    created_at: datetime


class AssetIssueDetailOut(Schema):
    """A report with its conversation, for its detail page (IT and reporter)."""

    id: UUID
    kind: str
    description: str
    status: str
    created_at: datetime
    resolved_at: datetime | None
    reported_by: IssueReporterOut | None
    handled_by: UserRefOut | None
    # IT-internal: always empty for the reporter.
    assigned_team: TeamRefOut | None
    assignee: UserRefOut | None
    asset: IssueDeviceDetailOut
    entries: list[IssueEntryOut]
    other_issues: list[IssueSummaryOut]
    unseen_update: bool
    # The reporter still has the device (their device page can be opened).
    still_assigned: bool

    @staticmethod
    def resolve_assigned_team(obj, context):
        return obj.assigned_team if context_is_it_staff(context) else None

    @staticmethod
    def resolve_assignee(obj, context):
        return obj.assignee if context_is_it_staff(context) else None
