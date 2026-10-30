from datetime import timedelta

from django.utils import timezone

from apps.masterdata.models import Location


def handover_plan() -> dict[str, str]:
    """Date and place for marking a request ready: the ready message needs both."""
    return {
        "pickup_at": (timezone.now() + timedelta(days=1)).isoformat(),
        "pickup_location": str(Location.objects.get(code="HQ-IT-00").pk),
    }
