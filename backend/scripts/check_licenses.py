"""Fail if a production dependency has a license incompatible with Argus' AGPL-3.0-or-later.

    uv run python scripts/check_licenses.py        (in backend/; part of `just check-backend`)

Installs only the production dependencies from uv.lock into a throwaway venv, reads
their licenses with pip-licenses and checks them. Permissive licenses, LGPL, GPL-3.0 and
AGPL-3.0 are compatible (GPLv3 and AGPLv3 section 13), and so is GPL-2.0 "or later".
Incompatible: GPL-2.0-only, a GPL without a version (check it by hand and add it to ALLOW)
and SSPL. Alternatives ("MIT OR GPL-2.0", several classifiers) pass if one of them does.
"""

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SSPL = re.compile(r"SSPL|Server Side Public", re.IGNORECASE)
LESSER = re.compile(r"LGPL|Lesser General Public|Library General Public", re.IGNORECASE)
# Whole tokens only, so "LGPL" doesn't count as "GPL".
GPL = re.compile(r"(?<![A-Za-z])A?GPL|General Public License", re.IGNORECASE)
V3_OR_LATER = re.compile(r"v3|(?<![\d.])3(\.0)?(?![\d.])|or[- ]later|\+", re.IGNORECASE)
ALTERNATIVES = re.compile(r"\s+OR\s+|;\s*", re.IGNORECASE)

# Packages whose metadata is wrong or ambiguous, after checking them by hand: the package
# name as key, the reason as value.
ALLOW: dict[str, str] = {}

# pip-licenses and what it brings along; not part of the app.
TOOLING = ["pip-licenses", "prettytable", "wcwidth"]


def production_licenses() -> list[dict[str, str]]:
    with tempfile.TemporaryDirectory() as tmp:
        requirements = Path(tmp) / "requirements.txt"
        venv = Path(tmp) / "venv"
        bin_dir = venv / ("Scripts" if sys.platform == "win32" else "bin")
        run = ["uv", "--quiet"]
        subprocess.run(
            [
                *run,
                "export",
                "--locked",
                "--no-dev",
                "--no-hashes",
                "--format",
                "requirements.txt",
                "-o",
                str(requirements),
            ],
            check=True,
        )
        subprocess.run([*run, "venv", str(venv)], check=True)
        subprocess.run(
            [*run, "pip", "install", "--python", str(venv), "-r", str(requirements), *TOOLING[:1]],
            check=True,
        )
        output = subprocess.run(
            [str(bin_dir / "pip-licenses"), "--format=json", "--ignore-packages", *TOOLING],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    licenses: list[dict[str, str]] = json.loads(output)
    return licenses


def compatible(license_: str) -> bool:
    for alternative in ALTERNATIVES.split(license_.strip("() ")):
        parts = re.split(r"\s+AND\s+", alternative.strip("() "), flags=re.IGNORECASE)
        if all(compatible_part(part) for part in parts):
            return True
    return False


def compatible_part(license_: str) -> bool:
    if SSPL.search(license_):
        return False
    if LESSER.search(license_) or not GPL.search(license_):
        return True
    return bool(V3_OR_LATER.search(license_))


def main() -> int:
    bad = []
    for pkg in production_licenses():
        name, license_ = pkg["Name"], pkg.get("License", "")
        if name.lower() in ALLOW:
            continue
        if not compatible(license_):
            bad.append(f"{name} {pkg.get('Version', '')}: {license_}")
    for line in bad:
        print(f"incompatible license: {line}")
    if not bad:
        print("licenses ok")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
