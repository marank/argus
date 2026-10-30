from django.db.models import Model, Q, QuerySet
from django.db.models.expressions import Combinable

# Every word adds a condition per field; without a cap a pasted text builds a query
# too large for the database. Words beyond these limits are ignored.
MAX_SEARCH_LENGTH = 200
MAX_SEARCH_WORDS = 10


def search_words(term: str | None) -> list[str]:
    """The words of a search term, capped to what a search sensibly needs."""
    return (term or "")[:MAX_SEARCH_LENGTH].split()[:MAX_SEARCH_WORDS]


def search[M: Model, R](
    queryset: QuerySet[M, R], term: str | None, fields: tuple[str, ...]
) -> QuerySet[M, R]:
    """Case-insensitive OR search over ``fields``; every word must match."""
    if not term or not fields:
        return queryset
    for word in search_words(term):
        condition = Q()
        for field in fields:
            condition |= Q(**{f"{field}__icontains": word})
        queryset = queryset.filter(condition)
    return queryset.distinct()


def order[M: Model, R](
    queryset: QuerySet[M, R], ordering: str | None, allowed: tuple[str, ...]
) -> QuerySet[M, R]:
    """Apply a comma separated ordering, ignoring fields not in ``allowed``.

    Without a usable ordering the queryset's own (or the model's default) applies. The
    primary key always comes last: rows that tie on the sort fields would otherwise come
    back in any order, swapping places on reload and repeating or going missing between
    pages. UUIDv7 keys make that the order of creation.
    """
    fields: list[str | Combinable] = [f for f in (ordering or "").split(",") if f.lstrip("-") in allowed]
    base = fields or list(queryset.query.order_by) or list(queryset.model._meta.ordering or ())
    return queryset.order_by(*base, "pk")
