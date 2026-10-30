from apps.core.api.querying import order
from apps.inventory.models import Consumable
from apps.masterdata.models import Manufacturer


def test_the_primary_key_breaks_ties_of_a_requested_ordering():
    queryset = order(Manufacturer.objects.all(), "-name,unknown", ("name",))
    assert queryset.query.order_by == ("-name", "pk")


def test_without_a_usable_ordering_the_default_applies_with_the_tiebreaker():
    queryset = order(Consumable.objects.all(), "unknown", ("quantity",))
    assert queryset.query.order_by == ("model__name", "pk")


def test_an_ordering_given_by_the_view_is_kept():
    queryset = order(Consumable.objects.order_by("-quantity"), None, ("quantity",))
    assert queryset.query.order_by == ("-quantity", "pk")
