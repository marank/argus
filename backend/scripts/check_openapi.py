"""Fail if frontend/openapi.json no longer matches the API.

    uv run python scripts/check_openapi.py         (in backend/; part of `just check-backend`)

Exports the schema into a temporary file with the same command as `just api-schema` and
compares it with the committed file. It changes nothing in the working tree, so it also
passes with an uncommitted, but current, openapi.json.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

COMMITTED = Path(__file__).resolve().parents[2] / "frontend" / "openapi.json"


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "openapi.json"
        subprocess.run([sys.executable, "manage.py", "export_openapi", str(target)], check=True)
        current = target.read_text(encoding="utf-8")
    # Text mode: line endings may differ between a Windows checkout and the export.
    if not COMMITTED.exists() or COMMITTED.read_text(encoding="utf-8") != current:
        print("API changed: run `just api-types` and commit both files", file=sys.stderr)
        return 1
    print("openapi.json up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
