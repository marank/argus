"""Live update signals for devices, licenses, consumables and problem reports (see ``apps.core.live``)."""

from apps.core.live import Signal, track


def connect() -> None:
    from apps.inventory.models import (
        Asset,
        AssetEvent,
        AssetIssue,
        AssetIssueEntry,
        Consumable,
        ConsumableMovement,
        License,
        LicenseAssignment,
    )

    def asset(a: Asset) -> Signal:
        return "asset", a.pk, [a.assigned_to_id]

    def issue(i: AssetIssue) -> Signal:
        return "issue", i.pk, [i.reported_by_id]

    track(Asset, asset)
    track(AssetEvent, lambda event: asset(event.asset))
    track(AssetIssue, issue)
    track(AssetIssueEntry, lambda entry: issue(entry.issue))
    track(License, lambda license: ("license", license.pk, []))
    track(LicenseAssignment, lambda a: ("license", a.license_id, [a.user_id]))
    track(Consumable, lambda consumable: ("consumable", consumable.pk, []))
    track(ConsumableMovement, lambda movement: ("consumable", movement.consumable_id, []))
