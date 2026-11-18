import pytest

from apps.activity.models import Activity


@pytest.fixture
def fresh(demo) -> None:
    """Start with an empty log: the demo data wrote its own rows."""
    Activity.objects.all().delete()
