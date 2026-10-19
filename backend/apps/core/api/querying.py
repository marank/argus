from django.db.models import Q, QuerySet


def search(queryset: QuerySet, term: str | None, fields: tuple[str, ...]) -> QuerySet:
    """Case-insensitive OR search over ``fields``; every word must match."""
    if not term or not fields:
        return queryset
    for word in term.split():
        condition = Q()
        for field in fields:
            condition |= Q(**{f"{field}__icontains": word})
        queryset = queryset.filter(condition)
    return queryset.distinct()


def order(queryset: QuerySet, ordering: str | None, allowed: tuple[str, ...]) -> QuerySet:
    """Apply a comma separated ordering, ignoring fields not in ``allowed``."""
    if not ordering:
        return queryset
    fields = [f for f in ordering.split(",") if f.lstrip("-") in allowed]
    return queryset.order_by(*fields) if fields else queryset
