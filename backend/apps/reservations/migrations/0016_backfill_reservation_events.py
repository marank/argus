"""Fill the history of existing requests from what they recorded so far.

Only the latest state was kept before, so some steps cannot be restored: marking
ready (no date), earlier reminders, removed allocations and changed return dates.
"""

from django.db import migrations


def _name(user) -> str | None:
    if user is None:
        return None
    return f"{user.first_name} {user.last_name}".strip() or user.username


def _label(allocation) -> str:
    if allocation.asset_id:
        return allocation.asset.inventory_number
    model = (allocation.consumable or allocation.license).model
    name = f"{model.manufacturer.name} {model.name}"
    return f"{allocation.quantity}× {name}" if allocation.consumable_id else name


def _clean(data: dict) -> dict:
    return {key: value for key, value in data.items() if value not in (None, "", [])}


def backfill(apps, schema_editor):
    Reservation = apps.get_model("reservations", "Reservation")
    ReservationEvent = apps.get_model("reservations", "ReservationEvent")
    Allocation = apps.get_model("reservations", "ReservationAllocation")
    Handover = apps.get_model("reservations", "Handover")
    DeviceReturn = apps.get_model("reservations", "DeviceReturn")

    events = []

    def add(reservation, kind, at, actor=None, **data):
        if at is not None:
            events.append(
                ReservationEvent(reservation=reservation, kind=kind, at=at, actor=actor, data=_clean(data))
            )

    queryset = Reservation.objects.filter(events__isnull=True).select_related(
        "requester", "created_by", "approver", "reminded_by"
    )
    for r in queryset.iterator():
        allocations = list(
            Allocation.objects.filter(item__reservation=r).select_related(
                "asset",
                "consumable__model__manufacturer",
                "license__model__manufacturer",
            )
        )
        on_behalf = r.created_by_id and r.created_by_id != r.requester_id
        add(
            r,
            "direct" if r.origin == "direct" else "created",
            r.created_at,
            r.created_by,
            requester=_name(r.requester) if on_behalf else None,
        )
        if r.approval in ("approved", "rejected"):
            add(
                r,
                "approved" if r.approval == "approved" else "declined",
                r.approval_decided_at,
                r.approver,
                comment=r.approval_comment,
            )
        if r.confirmed_at and r.origin != "direct":
            add(r, "confirmed", r.confirmed_at, comment=r.it_comment)
        for a in allocations:
            add(r, "allocated", a.allocated_at, a.allocated_by, items=[_label(a)])

        handover = Handover.objects.filter(reservation=r).select_related("handed_out_by").first()
        if handover:
            add(
                r,
                "handed_out",
                handover.handed_out_at,
                handover.handed_out_by,
                method=handover.method,
                received_by=handover.received_by_name,
                location=handover.location,
                items=[_label(a) for a in allocations if a.handed_out_at],
            )
        for taken in DeviceReturn.objects.filter(reservation=r).select_related("returned_by"):
            back = [a for a in allocations if a.device_return_id == taken.pk]
            add(
                r,
                "returned",
                taken.returned_at,
                taken.returned_by,
                items=[_label(a) for a in back],
                damaged=[_label(a) for a in back if a.returned_damaged],
                notes=taken.notes,
            )
        if r.reminded_at:
            add(r, "reminded", r.reminded_at, r.reminded_by)

        if r.status == "cancelled":
            add(r, "cancelled", r.completed_at)
        elif r.status == "rejected" and r.approval != "rejected":
            add(r, "rejected", r.completed_at, comment=r.it_comment)
        elif r.status == "completed":
            # Permanent hand-outs, and those without anything to bring back, complete
            # with the hand-out itself; lent devices complete once they are back.
            lent = any(a.asset_id or a.license_id for a in allocations)
            if r.duration == "temporary" and lent and r.completed_at:
                # The request completes a moment before the return is written: keep it after.
                last_return = max(
                    (e.at for e in events if e.reservation is r and e.kind == "returned"), default=None
                )
                add(r, "completed", max(r.completed_at, last_return or r.completed_at))

    ReservationEvent.objects.bulk_create(events, batch_size=500)


class Migration(migrations.Migration):
    dependencies = [
        ("reservations", "0015_reservation_events"),
    ]

    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
