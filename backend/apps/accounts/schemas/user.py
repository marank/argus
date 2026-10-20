from uuid import UUID

from ninja import Schema

from apps.accounts.models import User
from apps.core.schemas import RefOut
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
    is_terminal: bool
    terminal_location: LocationRefOut | None
    is_active: bool
    is_ldap_user: bool


class CurrentUserOut(UserOut):
    language: str
    notification_settings: dict[str, bool]
    dashboard_settings: dict
    is_superuser: bool


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
    is_terminal: bool = False
    terminal_location: UUID | None = None
    is_active: bool = True


class PreferencesIn(Schema):
    language: User.Language | None = None
    # Email notifications the user switches off ({event: false}).
    notification_settings: dict[str, bool] | None = None
    # The own dashboard layout; an empty object restores the default.
    dashboard_settings: dict | None = None
