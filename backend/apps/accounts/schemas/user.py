from uuid import UUID

from ninja import Schema

from apps.accounts.models import User
from apps.core.schemas import RefOut


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
    is_active: bool


class CurrentUserOut(UserOut):
    language: str


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
    is_active: bool = True


class PreferencesIn(Schema):
    language: User.Language | None = None
