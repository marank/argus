from django.core.management import call_command
from django.utils import timezone

from apps.accounts.models import Team, User
from apps.inventory.models import Asset, AssetIssue, License
from apps.procurement.models import PurchaseOrder
from apps.reservations.models import Reservation


def test_full_demo_data_covers_every_state(db):
    """The complete demo data runs through and shows every state at least once."""
    call_command("seed_demo", verbosity=0)

    assert User.objects.count() > 25
    assert Asset.objects.count() > 140
    reservation_states = set(Reservation.objects.values_list("status", flat=True))
    assert reservation_states == set(Reservation.Status.values)
    # One lent request is overdue.
    assert Reservation.objects.filter(
        status=Reservation.Status.HANDED_OUT, end_date__lt=timezone.localdate()
    ).exists()
    assert set(Asset.objects.values_list("status", flat=True)) == set(Asset.Status.values)
    assert set(PurchaseOrder.objects.values_list("status", flat=True)) == set(PurchaseOrder.Status.values)
    assert set(AssetIssue.objects.values_list("status", flat=True)) == set(AssetIssue.Status.values)
    assert any(license.is_expired for license in License.objects.all())

    # Teams: requests routed by model and default, every tab of the lists filled.
    assert Team.objects.get(is_default=True).name == "IT-Support"
    ledgerline = Reservation.objects.get(title="Ledgerline access for the monthly reports")
    assert ledgerline.assigned_team.name == "Ledgerline"
    assert Reservation.objects.filter(assigned_team__isnull=True, assignee__isnull=True).exists()
    assert Reservation.objects.filter(assignee__username="jkoch").exists()
    assert AssetIssue.objects.filter(assignee__username="it").exists()
