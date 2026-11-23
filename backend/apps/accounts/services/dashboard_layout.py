"""The user's own dashboard layout (``User.dashboard_settings``).

The frontend owns the widget and card ids; the backend only keeps well-formed entries
and bounds their size.
"""

import json
from enum import StrEnum
from typing import Any, NotRequired, TypedDict


class WidgetSize(StrEnum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class WidgetHeight(StrEnum):
    """``auto`` fits the content (and the row); the others are fixed heights that scroll."""

    AUTO = "auto"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class Widget(TypedDict):
    id: str
    # Further instances of a widget name the widget they show; the first has its id.
    widget: NotRequired[str]
    visible: bool
    size: WidgetSize
    height: WidgetHeight
    # Cards of a key figure panel the user switched off.
    hidden_cards: list[str]
    # Cards in the user's order; empty keeps the default order.
    card_order: list[str]
    # The widget's own settings, such as the text of the notes widget.
    options: dict[str, Any]


class Layout(TypedDict, total=False):
    # In the order on screen; missing or empty means the default layout.
    widgets: list[Widget]


# Room for a widget's own settings.
WIDGET_OPTIONS_MAX = 10_000


def card_keys(value: object) -> list[str]:
    """Distinct card keys in their given order."""
    if not isinstance(value, list):
        return []
    return list(dict.fromkeys(c for c in value if isinstance(c, str) and 0 < len(c) <= 50))[:50]


def widget_options(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or len(json.dumps(value, ensure_ascii=False)) > WIDGET_OPTIONS_MAX:
        return {}
    return value


def _clean_widget(entry: dict[Any, Any], widget_id: str) -> Widget:
    """The widget of an entry whose id was checked, with defaults for invalid values."""
    widget: Widget = {
        "id": widget_id,
        "visible": bool(entry.get("visible", True)),
        "size": WidgetSize(entry["size"]) if entry.get("size") in WidgetSize else WidgetSize.LARGE,
        "height": (
            WidgetHeight(entry["height"]) if entry.get("height") in WidgetHeight else WidgetHeight.AUTO
        ),
        "hidden_cards": card_keys(entry.get("hidden_cards")),
        "card_order": card_keys(entry.get("card_order")),
        "options": widget_options(entry.get("options")),
    }
    kind = entry.get("widget")
    if isinstance(kind, str) and 0 < len(kind) <= 50:
        widget["widget"] = kind
    return widget


def clean(value: object) -> Layout:
    """Keeps only well-formed widget entries."""
    widgets: list[Widget] = []
    seen: set[str] = set()
    entries = value.get("widgets") if isinstance(value, dict) else None
    for entry in entries if isinstance(entries, list) else []:
        if not isinstance(entry, dict):
            continue
        widget_id = entry.get("id")
        if not isinstance(widget_id, str) or not widget_id or len(widget_id) > 50 or widget_id in seen:
            continue
        seen.add(widget_id)
        widgets.append(_clean_widget(entry, widget_id))
    return {"widgets": widgets[:50]} if widgets else {}
