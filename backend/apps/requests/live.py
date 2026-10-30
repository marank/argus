"""Live update signals for requests (see ``apps.core.live``)."""

from apps.core.live import Signal, track


def connect() -> None:
    from apps.requests.models import (
        AssetRequest,
        AssetRequestAllocation,
        AssetRequestEvent,
        AssetRequestItem,
        AssetRequestStatus,
        DeviceReturn,
        Handover,
    )

    def asset_request(r: AssetRequest) -> Signal:
        # The requester, whoever decided the approval and, while it waits, everyone who may approve.
        users = [r.requester_id, r.approver_id]
        if r.status == AssetRequestStatus.PENDING_APPROVAL:
            users += r.approvers().values_list("pk", flat=True)
        return "request", r.pk, users

    track(AssetRequest, asset_request)
    track(AssetRequestItem, lambda item: asset_request(item.asset_request))
    track(AssetRequestAllocation, lambda allocation: asset_request(allocation.item.asset_request))
    track(AssetRequestEvent, lambda event: asset_request(event.asset_request))
    track(Handover, lambda handover: asset_request(handover.asset_request))
    track(DeviceReturn, lambda device_return: asset_request(device_return.asset_request))
