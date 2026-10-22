from django.core.management import call_command
from django.utils import timezone

from apps.accounts.models import Team, User
from apps.inventory.models import Asset, AssetIssue, License
from apps.procurement.models import PurchaseOrder
from apps.requests.models import AssetRequest


def test_full_demo_data_covers_every_state(db):
    """The complete demo data runs through and shows every state at least once."""
    call_command("seed_demo", verbosity=0)

    assert User.objects.count() > 25
    assert Asset.objects.count() > 140
    asset_request_states = set(AssetRequest.objects.values_list("status", flat=True))
    assert asset_request_states == set(AssetRequest.Status.values)
    # One lent request is overdue.
    assert AssetRequest.objects.filter(
        status=AssetRequest.Status.HANDED_OUT, end_date__lt=timezone.localdate()
    ).exists()
    assert set(Asset.objects.values_list("status", flat=True)) == set(Asset.Status.values)
    assert set(PurchaseOrder.objects.values_list("status", flat=True)) == set(PurchaseOrder.Status.values)
    assert set(AssetIssue.objects.values_list("status", flat=True)) == set(AssetIssue.Status.values)
    assert any(license.is_expired for license in License.objects.all())

    # Teams: requests routed by model and default, every tab of the lists filled.
    assert Team.objects.get(is_default=True).name == "IT-Support"
    ledgerline = AssetRequest.objects.get(title="Ledgerline access for the monthly reports")
    assert ledgerline.assigned_team.name == "Ledgerline"
    assert AssetRequest.objects.filter(assigned_team__isnull=True, assignee__isnull=True).exists()
    assert AssetRequest.objects.filter(assignee__username="jkoch").exists()
    assert AssetIssue.objects.filter(assignee__username="it").exists()


def test_seeding_keeps_the_password_of_existing_accounts(db):
    User.objects.create_superuser("admin", password="the-real-one")
    call_command("seed_demo", verbosity=0)
    admin = User.objects.get(username="admin")
    assert admin.check_password("the-real-one")
    assert not admin.check_password("argus-demo")
    assert User.objects.get(username="employee").check_password("argus-demo")
