"""Live update signals for purchase orders (see ``apps.core.live``)."""

from apps.core.live import track


def connect() -> None:
    from apps.procurement.models import PurchaseOrder, PurchaseOrderLine

    track(PurchaseOrder, lambda order: ("order", order.pk, []))
    track(PurchaseOrderLine, lambda line: ("order", line.order_id, []))
