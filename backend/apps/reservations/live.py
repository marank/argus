"""Live update signals for requests (see ``apps.core.live``)."""

from apps.core.live import track


def connect() -> None:
    from apps.reservations.models import (
        DeviceReturn,
        Handover,
        Reservation,
        ReservationAllocation,
        ReservationEvent,
        ReservationItem,
    )

    def reservation(r):
        # The requester, whoever decided the approval and, while it waits, everyone who may approve.
        users = [r.requester_id, r.approver_id]
        if r.status == Reservation.Status.PENDING_APPROVAL:
            users += r.approvers().values_list("pk", flat=True)
        return "reservation", r.pk, users

    track(Reservation, reservation)
    track(ReservationItem, lambda item: reservation(item.reservation))
    track(ReservationAllocation, lambda allocation: reservation(allocation.item.reservation))
    track(ReservationEvent, lambda event: reservation(event.reservation))
    track(Handover, lambda handover: reservation(handover.reservation))
    track(DeviceReturn, lambda device_return: reservation(device_return.reservation))
