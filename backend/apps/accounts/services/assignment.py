"""Who is responsible for a request or a problem report: a team, a person, both or neither.

Models taking part have two optional foreign keys, ``assigned_team`` and ``assignee``.
"""

from typing import Literal
from uuid import UUID

from django.db.models import Q
from django.utils.translation import gettext as _

from apps.accounts.models import Team, User
from apps.core.exceptions import BusinessError

# Quick filters of the IT lists: assigned to me, to one of my teams (or me), to nobody.
Assigned = Literal["me", "my_teams", "nobody"]


def resolve_assignment(team_id: UUID | None, assignee_id: UUID | None) -> tuple[Team | None, User | None]:
    team = Team.objects.filter(pk=team_id).first() if team_id else None
    if team_id and team is None:
        raise BusinessError(_("Unknown team."))
    assignee = User.objects.filter(pk=assignee_id, is_active=True).first() if assignee_id else None
    if assignee_id and (assignee is None or not assignee.is_it_staff):
        raise BusinessError(_("Only active IT staff can be assigned."))
    return team, assignee


def assign(obj, team_id: UUID | None, assignee_id: UUID | None):
    """Set team and assignee of ``obj``; either may stay empty."""
    obj.assigned_team, obj.assignee = resolve_assignment(team_id, assignee_id)
    obj.save(update_fields=["assigned_team", "assignee", "updated_at"])
    return obj


def assigned_q(user: User, assigned: Assigned | None) -> Q:
    if assigned == "me":
        return Q(assignee=user)
    if assigned == "my_teams":
        # A subquery, so a team with several members does not repeat rows.
        return Q(assigned_team__in=user.teams.all()) | Q(assignee=user)
    if assigned == "nobody":
        return Q(assigned_team__isnull=True, assignee__isnull=True)
    return Q()
