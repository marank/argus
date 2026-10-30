"""Who is responsible for a request or a problem report: a team, a person, both or neither.

Models taking part have two optional foreign keys, ``assigned_team`` and ``assignee``.
"""

from collections.abc import Iterable
from typing import Literal, Protocol
from uuid import UUID

from django.db.models import Q, QuerySet
from django.utils.translation import gettext as _

from apps.accounts.models import Team, User
from apps.core.exceptions import BusinessError

# Quick filters of the IT lists: assigned to me, to one of my teams (or me), to nobody.
Assigned = Literal["me", "my_teams", "nobody"]


class Assignable(Protocol):
    """A model with ``assigned_team`` and ``assignee`` (and ``updated_at``)."""

    assigned_team: Team | None
    assignee: User | None

    @property
    def assigned_team_id(self) -> UUID | None: ...

    @property
    def assignee_id(self) -> UUID | None: ...

    def save(self, *, update_fields: Iterable[str] | None = None) -> None: ...


def resolve_assignment(team_id: UUID | None, assignee_id: UUID | None) -> tuple[Team | None, User | None]:
    team = Team.objects.filter(pk=team_id).first() if team_id else None
    if team_id and team is None:
        raise BusinessError(_("Unknown team."))
    assignee = User.objects.filter(pk=assignee_id, is_active=True).first() if assignee_id else None
    if assignee_id and (assignee is None or not assignee.is_it_staff):
        raise BusinessError(_("Only active IT staff can be assigned."))
    return team, assignee


def assign(obj: Assignable, team_id: UUID | None, assignee_id: UUID | None, by: User) -> bool:
    """Set team and assignee of ``obj``; either may stay empty.

    Returns whether someone else than ``by`` became the assignee (and should hear of it).
    """
    previous = obj.assignee_id
    obj.assigned_team, obj.assignee = resolve_assignment(team_id, assignee_id)
    obj.save(update_fields=["assigned_team", "assignee", "updated_at"])
    return obj.assignee_id is not None and obj.assignee_id not in (previous, by.pk)


def route(candidates: Iterable[Team | None]) -> Team | None:
    """The team for something new: the first candidate (from its models or categories),
    otherwise the default team."""
    return next((team for team in candidates if team), None) or Team.objects.filter(is_default=True).first()


def responsible_staff(obj: Assignable) -> QuerySet[User]:
    """Who hears of something new: the assignee and the members of its team, or all of
    IT while nobody is responsible (or the team has no active IT members)."""
    from apps.core.notifications import it_staff

    staff = it_staff()
    responsible = Q()
    if obj.assigned_team_id:
        responsible |= Q(teams=obj.assigned_team_id)
    if obj.assignee_id:
        responsible |= Q(pk=obj.assignee_id)
    if responsible:
        people = staff.filter(responsible).distinct()
        if people.exists():
            return people
    return staff


def assigned_q(user: User, assigned: Assigned | None) -> Q:
    if assigned == "me":
        return Q(assignee=user)
    if assigned == "my_teams":
        # A subquery, so a team with several members does not repeat rows.
        return Q(assigned_team__in=user.teams.all()) | Q(assignee=user)
    if assigned == "nobody":
        return Q(assigned_team__isnull=True, assignee__isnull=True)
    return Q()
