from typing import Any
from uuid import UUID

from apps.accounts.models import Role, Team, TwoFactorMethod, User
from apps.accounts.permissions import PermissionLevel, ResourceKey
from apps.accounts.services import dashboard_layout
from apps.accounts.services.dashboard_layout import WidgetHeight, WidgetSize
from apps.core.api.security import context_is_it_staff
from apps.core.notifications import NotificationEvent, known_events
from apps.core.schemas import RefOut
from apps.core.schemas.base import Schema
from apps.masterdata.schemas.refs import LocationRefOut


class UserRefOut(Schema):
    id: UUID
    username: str
    display_name: str


class UserOut(Schema):
    id: UUID
    username: str
    first_name: str
    last_name: str
    display_name: str
    email: str
    employee_number: str
    job_title: str
    phone: str
    department: RefOut | None
    is_it_staff: bool
    is_superuser: bool
    is_terminal: bool
    terminal_location: LocationRefOut | None
    is_active: bool
    is_ldap_user: bool
    approval_exempt: bool
    # Method of the second sign-in step ("email", "totp") or None; only for IT and the user.
    two_factor: TwoFactorMethod | None = None
    # IT staff's roles and teams; only sent to IT staff.
    roles: list[RefOut] = []
    teams: list[RefOut] = []

    @staticmethod
    def resolve_roles(obj: User, context: dict[str, Any] | None) -> list[Role]:
        return list(obj.roles.all()) if context_is_it_staff(context) else []

    @staticmethod
    def resolve_teams(obj: User, context: dict[str, Any] | None) -> list[Team]:
        return list(obj.teams.all()) if context_is_it_staff(context) else []

    @staticmethod
    def resolve_two_factor(obj: User, context: dict[str, Any] | None) -> str | None:
        request = (context or {}).get("request")
        if not (context_is_it_staff(context) or (request and request.user.pk == obj.pk)):
            return None
        two_factor = getattr(obj, "two_factor", None)
        return two_factor.method if two_factor else None


class DashboardWidgetOut(Schema):
    id: str
    # Further instances of a widget name the widget they show; null on the first.
    widget: str | None = None
    visible: bool
    size: WidgetSize
    height: WidgetHeight
    # Cards of a key figure panel the user switched off.
    hidden_cards: list[str]
    # Cards in the user's order; empty keeps the default order.
    card_order: list[str]
    # The widget's own settings, such as the text of the notes widget.
    options: dict[str, Any]


class DashboardLayoutOut(Schema):
    # In the order on screen; empty means the default layout.
    widgets: list[DashboardWidgetOut] = []


class CurrentUserOut(UserOut):
    # Area → "read" or "write" from the user's roles (everything for administrators).
    permissions: dict[ResourceKey, PermissionLevel]
    language: User.Language
    theme: User.Theme
    # Notifications the user switched off, by email and in the app.
    notification_settings: dict[NotificationEvent, bool]
    app_notification_settings: dict[NotificationEvent, bool]
    dashboard_settings: DashboardLayoutOut
    # Decides on requests of at least one department (shows the approvals page).
    is_approver: bool

    @staticmethod
    def resolve_notification_settings(obj: User) -> dict[NotificationEvent, bool]:
        return known_events(obj.notification_settings)

    @staticmethod
    def resolve_app_notification_settings(obj: User) -> dict[NotificationEvent, bool]:
        return known_events(obj.app_notification_settings)

    @staticmethod
    def resolve_dashboard_settings(obj: User) -> dashboard_layout.Layout:
        return dashboard_layout.clean(obj.dashboard_settings)


class UserIn(Schema):
    username: str
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    employee_number: str = ""
    job_title: str = ""
    phone: str = ""
    department: UUID | None = None
    is_staff: bool = False
    # Administrator; only administrators may change it. None leaves it as it is.
    is_superuser: bool | None = None
    # Only administrators assign roles; teams need the right to edit teams. None leaves them.
    roles: list[UUID] | None = None
    teams: list[UUID] | None = None
    is_terminal: bool = False
    terminal_location: UUID | None = None
    is_active: bool = True
    approval_exempt: bool = False


class PreferencesIn(Schema):
    language: User.Language | None = None
    theme: User.Theme | None = None
    # Notifications the user switches off ({event: false}), by email and in the app.
    notification_settings: dict[str, bool] | None = None
    app_notification_settings: dict[str, bool] | None = None
    # The own dashboard layout; an empty object restores the default.
    dashboard_settings: dict[str, Any] | None = None
