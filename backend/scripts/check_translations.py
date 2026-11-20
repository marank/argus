"""Fail when a backend text is untranslated or fuzzy, or django.mo is out of date.

    uv run --with polib python scripts/check_translations.py   (in backend/; part of `just check-backend`)

With the gettext tools installed, `makemessages` first adds the strings from the code to the
.po files; they are put back afterwards, so the check changes nothing in the working tree.
Without them (e.g. on Windows) only the committed .po files are checked, with a warning;
`--require-gettext` (passed by the justfile in CI) fails instead. The committed django.mo
must match its .po file (`just compile-messages`).
"""

import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import polib

PO_FILES = sorted(Path("locale").glob("*/LC_MESSAGES/django.po"))


def catalog(entries: Iterable[Any]) -> dict[tuple[str, str, str], str]:
    """What gettext looks up: (context, text, plural) -> translation(s), from polib entries."""

    def value(entry: Any) -> str:
        return "\0".join(entry.msgstr_plural[n] for n in sorted(entry.msgstr_plural)) or entry.msgstr

    return {(e.msgctxt or "", e.msgid, e.msgid_plural or ""): value(e) for e in entries if e.msgid}


def outdated_mo(po_path: Path) -> list[str]:
    mo_path = po_path.with_suffix(".mo")
    translated = catalog(polib.pofile(str(po_path)).translated_entries())
    if mo_path.exists() and catalog(polib.mofile(str(mo_path))) == translated:
        return []
    return [f"{mo_path}: does not match {po_path.name}; run `just compile-messages`"]


def incomplete(po_path: Path) -> list[str]:
    po = polib.pofile(str(po_path))
    return [f"{po_path}: untranslated: {e.msgid}" for e in po.untranslated_entries()] + [
        f"{po_path}: fuzzy: {e.msgid}" for e in po.fuzzy_entries()
    ]


def collect_and_check() -> list[str]:
    """makemessages, check the result, then restore the committed .po files."""
    with tempfile.TemporaryDirectory() as backup:
        copies = {path: Path(backup) / str(index) for index, path in enumerate(PO_FILES)}
        for path, copy in copies.items():
            shutil.copyfile(path, copy)
        try:
            subprocess.run(
                [sys.executable, "manage.py", "makemessages", "-l", "de", "--ignore", ".venv/*", "--no-wrap"],
                check=True,
                capture_output=True,
            )
            return [line for path in PO_FILES for line in incomplete(path)]
        finally:
            for path, copy in copies.items():
                shutil.copyfile(copy, path)


def main() -> int:
    found = [line for path in PO_FILES for line in outdated_mo(path)]
    if shutil.which("xgettext"):
        found += collect_and_check()
    elif "--require-gettext" in sys.argv:
        print("gettext tools (xgettext) missing", file=sys.stderr)
        return 1
    else:
        print("warning: gettext not installed; new strings in the code are not checked", file=sys.stderr)
        found += [line for path in PO_FILES for line in incomplete(path)]
    for line in found:
        print(line)
    print("translations incomplete" if found else "translations complete")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
