"""Import devices from a table (CSV export of an MDM, a spreadsheet, ...).

The frontend reads the file and maps its columns to device fields; each row arrives here
as ``{field: text}``. A row creates a device, or updates the one it matches (by serial
number, inventory number, ...). Rows go through the same services as the forms, so the
same rules and events apply.

The preview is the import itself, rolled back at the end: it shows exactly what the import
would do, including the inventory numbers new devices would get and every error.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, TypedDict
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.utils import translation
from django.utils.text import capfirst
from django.utils.translation import gettext as _

from apps.accounts.models import User
from apps.core.exceptions import BusinessError
from apps.inventory.models import Asset, AssetStatus
from apps.inventory.services import assets as asset_service
from apps.inventory.services.mac_address import normalize_mac_address
from apps.masterdata.models import AssetModel, Location, Supplier


class ImportField(models.TextChoices):
    """Device fields a column can be mapped to."""

    INVENTORY_NUMBER = "inventory_number"
    SERIAL_NUMBER = "serial_number"
    IDENTIFIER = "identifier"
    IMEI = "imei"
    MAC_ADDRESS = "mac_address"
    NAME = "name"
    MODEL = "model"
    STATUS = "status"
    CONDITION = "condition"
    LOCATION = "location"
    ASSIGNED_TO = "assigned_to"
    SUPPLIER = "supplier"
    PURCHASE_DATE = "purchase_date"
    PURCHASE_PRICE = "purchase_price"
    WARRANTY_UNTIL = "warranty_until"
    NOTES = "notes"


class ImportMatch(models.TextChoices):
    """Fields that identify an existing device."""

    SERIAL_NUMBER = "serial_number"
    INVENTORY_NUMBER = "inventory_number"
    IMEI = "imei"
    MAC_ADDRESS = "mac_address"
    NAME = "name"


class ImportAction(models.TextChoices):
    CREATE = "create"
    UPDATE = "update"
    UNCHANGED = "unchanged"
    SKIP = "skip"
    ERROR = "error"


class ExistingDevices(models.TextChoices):
    """What happens to a row that matches a device already in the inventory."""

    UPDATE = "update"
    SKIP = "skip"


class ImportDefaults(TypedDict, total=False):
    """Values for new devices whose row leaves the field empty."""

    model: UUID | None
    location: UUID | None
    status: str | None
    condition: str | None


class Change(TypedDict):
    field: str
    old: str
    new: str


class RowResult(TypedDict):
    row: int
    action: str
    asset_id: UUID | None
    inventory_number: str
    model: str
    changes: list[Change]
    errors: list[str]


class ImportResult(TypedDict):
    rows: list[RowResult]
    created: int
    updated: int
    unchanged: int
    skipped: int
    failed: int


# Exports guard text cells against spreadsheet formulas with a leading apostrophe and
# write "--" or "-" for no value (e.g. Fleetwise MDM: "'--").
EMPTY = re.compile(r"^[-–—]*$")
DATE_FORMATS = ("%Y-%m-%d", "%d.%m.%Y", "%d.%m.%y", "%d/%m/%Y", "%Y/%m/%d")


def clean_cell(value: str | None) -> str:
    text = (value or "").strip()
    if text.startswith("'"):
        text = text[1:].strip()
    return "" if EMPTY.match(text) else text


class RowError(Exception):
    pass


def _label(name: str) -> str:
    field = Asset._meta.get_field(name)
    return str(getattr(field, "verbose_name", name))


def _parse_date(text: str) -> date:
    head = re.split(r"[\sT]", text, maxsplit=1)[0]
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(head, fmt).date()
        except ValueError:
            continue
    raise RowError(_("“%(value)s” is not a date (e.g. 2026-03-31 or 31.03.2026).") % {"value": text})


def _parse_decimal(text: str) -> Decimal:
    number = re.sub(r"[^\d,.\-]", "", text)
    if "," in number and "." in number:
        # The separator further right is the decimal one: 1.234,56 or 1,234.56.
        thousands = "." if number.rfind(",") > number.rfind(".") else ","
        number = number.replace(thousands, "")
    number = number.replace(",", ".")
    try:
        return Decimal(number)
    except InvalidOperation:
        raise RowError(_("“%(value)s” is not a number.") % {"value": text}) from None


def _choice(choices: type[models.TextChoices], text: str) -> str:
    """A choice by its value or its label in English or German."""
    wanted = text.casefold()
    for value, label in choices.choices:
        if wanted == value.casefold():
            return value
        for language in ("en", "de"):
            with translation.override(language):
                if wanted == str(label).casefold():
                    return value
    raise RowError(
        _("“%(value)s” is not one of: %(choices)s.")
        % {"value": text, "choices": ", ".join(str(label) for _value, label in choices.choices)}
    )


@dataclass
class Lookups:
    """Finds models, locations, people and suppliers by name; remembers what it found."""

    cache: dict[tuple[str, str], Any] = field(default_factory=dict)

    def _one[M: models.Model](self, kind: str, text: str, queryset: models.QuerySet[M], q: Q) -> M:
        key = (kind, text.casefold())
        if key not in self.cache:
            found = list(queryset.filter(q)[:2])
            if not found:
                raise RowError(
                    _("%(field)s “%(value)s” not found.") % {"field": capfirst(_label(kind)), "value": text}
                )
            if len(found) > 1:
                raise RowError(
                    _("%(field)s “%(value)s” is ambiguous.")
                    % {"field": capfirst(_label(kind)), "value": text}
                )
            self.cache[key] = found[0]
        result: M = self.cache[key]
        return result

    def model(self, text: str) -> AssetModel:
        models_ = AssetModel.objects.filter(tracking=AssetModel.Tracking.SERIALIZED).select_related(
            "manufacturer", "category"
        )
        q = Q(name__iexact=text) | Q(designation__iexact=text) | Q(part_number__iexact=text)
        if text.isdigit():
            q |= Q(ean=text)
        try:
            return self._one("model", text, models_, q)
        except RowError:
            # "Handtec HT60": manufacturer and name in one cell.
            manufacturer, _sep, name = text.partition(" ")
            q = Q(manufacturer__name__iexact=manufacturer) & (
                Q(name__iexact=name) | Q(designation__iexact=name)
            )
            if not name:
                raise
            return self._one("model", text, models_, q)

    def location(self, text: str) -> Location:
        return self._one(
            "location", text, Location.objects.all(), Q(name__iexact=text) | Q(code__iexact=text)
        )

    def user(self, text: str) -> User:
        q = Q(username__iexact=text) | Q(email__iexact=text)
        if "," in text:
            last, _sep, first = text.partition(",")
            q |= Q(first_name__iexact=first.strip(), last_name__iexact=last.strip())
        elif " " in text:
            first, _sep, last = text.rpartition(" ")
            q |= Q(first_name__iexact=first.strip(), last_name__iexact=last.strip())
        return self._one("assigned_to", text, User.objects.all(), q)

    def supplier(self, text: str) -> Supplier:
        return self._one("supplier", text, Supplier.objects.all(), Q(name__iexact=text))


def _parse(name: str, text: str, lookups: Lookups) -> Any:
    parsers: dict[str, Callable[[str], Any]] = {
        "model": lookups.model,
        "location": lookups.location,
        "assigned_to": lookups.user,
        "supplier": lookups.supplier,
        "status": lambda t: _choice(AssetStatus, t),
        "condition": lambda t: _choice(Asset.Condition, t),
        "purchase_date": _parse_date,
        "warranty_until": _parse_date,
        "purchase_price": _parse_decimal,
        "mac_address": normalize_mac_address,
    }
    parser = parsers.get(name)
    return parser(text) if parser else text


def _display(asset: Asset, name: str) -> str:
    """The value of a field as the preview shows it."""
    value = getattr(asset, name)
    if value is None:
        return ""
    if name in ("status", "condition"):
        return str(getattr(asset, f"get_{name}_display")())
    if name == "model":
        return str(value.full_name)
    if name == "location":
        return str(value.full_name)
    if name == "assigned_to":
        return str(value.get_full_name() or value.username)
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _as_data(values: dict[str, Any]) -> dict[str, Any]:
    """Field values for the asset services: related objects by their id."""
    return {name: value.pk if isinstance(value, models.Model) else value for name, value in values.items()}


def _messages(exc: ValidationError) -> list[str]:
    if hasattr(exc, "error_dict"):
        return [
            f"{capfirst(_label(name))}: {message}" if name in ImportField.values else str(message)
            for name, messages in exc.message_dict.items()
            for message in messages
        ]
    return [str(message) for message in exc.messages]


def _find(match_by: str | None, values: dict[str, Any], ignore_case: bool = False) -> Asset | None:
    """The device whose ``match_by`` field equals the row's value, optionally in any case."""
    key = values.get(match_by) if match_by else None
    if not key or not match_by:
        return None
    found = list(
        Asset.objects.filter(**{f"{match_by}__iexact" if ignore_case else match_by: key}).select_related(
            "model__manufacturer"
        )[:3]
    )
    model = values.get("model")
    if len(found) > 1 and model is not None:
        found = [asset for asset in found if asset.model_id == model.pk]
    if len(found) > 1:
        raise RowError(
            _("Several devices have the %(field)s “%(value)s”.") % {"field": _label(match_by), "value": key}
        )
    return found[0] if found else None


def _changes(asset: Asset, names: list[str]) -> list[Change]:
    return [
        {"field": name, "old": "", "new": _display(asset, name)} for name in names if _display(asset, name)
    ]


class _Importer:
    def __init__(
        self, user: User, defaults: ImportDefaults, match_by: str | None, existing: str, ignore_case: bool
    ) -> None:
        self.user, self.defaults, self.match_by, self.existing = user, defaults, match_by, existing
        self.ignore_case = ignore_case
        self.lookups = Lookups()
        self.default_values: dict[str, Any] = {}
        if model_id := defaults.get("model"):
            self.default_values["model"] = AssetModel.objects.select_related("manufacturer").get(pk=model_id)
        if location_id := defaults.get("location"):
            self.default_values["location"] = Location.objects.get(pk=location_id)
        for name in ("status", "condition"):
            if value := defaults.get(name):
                self.default_values[name] = value

    def row(self, index: int, cells: dict[str, str]) -> RowResult:
        result: RowResult = {
            "row": index,
            "action": ImportAction.ERROR,
            "asset_id": None,
            "inventory_number": "",
            "model": "",
            "changes": [],
            "errors": [],
        }
        values: dict[str, Any] = {}
        for name, raw in cells.items():
            text = clean_cell(raw)
            if not text or name not in ImportField.values:
                continue
            try:
                values[name] = _parse(name, text, self.lookups)
            except RowError as exc:
                result["errors"].append(str(exc))
        if result["errors"]:
            return result
        try:
            with transaction.atomic():
                existing = _find(self.match_by, values, self.ignore_case)
                if existing is None:
                    self._create(values, result)
                elif self.existing == ExistingDevices.SKIP:
                    self._describe(existing, result, ImportAction.SKIP)
                else:
                    self._update(existing, values, result)
        except RowError as exc:
            result["errors"].append(str(exc))
        except BusinessError as exc:
            result["errors"].append(exc.message)
        except ValidationError as exc:
            result["errors"].extend(_messages(exc))
        if result["errors"]:
            result["action"] = ImportAction.ERROR
        return result

    @staticmethod
    def _describe(asset: Asset, result: RowResult, action: str) -> None:
        result["action"] = action
        result["asset_id"] = asset.pk
        result["inventory_number"] = asset.inventory_number
        result["model"] = asset.model.full_name

    def _create(self, values: dict[str, Any], result: RowResult) -> None:
        values = {**self.default_values, **values}
        if "model" not in values:
            raise RowError(_("No model: map a column to the model or choose one for all new devices."))
        asset = asset_service.create_asset(_as_data(values), self.user)
        self._describe(asset, result, ImportAction.CREATE)
        result["changes"] = _changes(asset, [name for name in ImportField.values if name in values])

    def _update(self, asset: Asset, values: dict[str, Any], result: RowResult) -> None:
        before = {name: _display(asset, name) for name in values}
        changed = {
            name: value
            for name, value in values.items()
            if _display(_with(asset, name, value), name) != before[name]
        }
        if not changed:
            self._describe(asset, result, ImportAction.UNCHANGED)
            return
        asset_service.update_asset(asset, _as_data(changed), self.user)
        self._describe(asset, result, ImportAction.UPDATE)
        result["changes"] = [
            {"field": name, "old": before[name], "new": _display(asset, name)} for name in changed
        ]


def _with(asset: Asset, name: str, value: Any) -> Asset:
    """A copy of ``asset`` with one field set, to compare how it would show."""
    copy = Asset(**{f.attname: getattr(asset, f.attname) for f in Asset._meta.concrete_fields})
    setattr(copy, name, value)
    return copy


MAX_ROWS = 2000


def import_assets(
    rows: list[dict[str, str]],
    user: User,
    *,
    defaults: ImportDefaults | None = None,
    match_by: str | None = ImportMatch.SERIAL_NUMBER,
    existing: str = ExistingDevices.UPDATE,
    ignore_case: bool = False,
    dry_run: bool = False,
) -> ImportResult:
    """Create or update a device per row; rows with errors are left out.

    ``ignore_case`` finds "31415a926b" also as "31415A926B".
    ``dry_run`` rolls everything back, for the preview.
    """
    if len(rows) > MAX_ROWS:
        raise BusinessError(_("A file can hold at most %(count)d devices.") % {"count": MAX_ROWS})
    with transaction.atomic():
        importer = _Importer(user, defaults or {}, match_by, existing, ignore_case)
        results = [importer.row(index, cells) for index, cells in enumerate(rows, start=1)]
        if dry_run:
            transaction.set_rollback(True)
            for result in results:
                if result["action"] == ImportAction.CREATE:
                    result["asset_id"] = None  # rolled back
    counts = {action: sum(1 for r in results if r["action"] == action) for action in ImportAction.values}
    return {
        "rows": results,
        "created": counts[ImportAction.CREATE],
        "updated": counts[ImportAction.UPDATE],
        "unchanged": counts[ImportAction.UNCHANGED],
        "skipped": counts[ImportAction.SKIP],
        "failed": counts[ImportAction.ERROR],
    }
