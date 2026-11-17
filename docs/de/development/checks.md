# Prüfungen und Tests

Der VS-Code-Task **Check: all** führt dieselben Prüfungen aus wie die CI und muss vor einem
Push bestehen. Von Hand:

```bash
cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy . && uv run deptry . && uv run pytest --cov
```

```bash
cd frontend && pnpm lint && pnpm format:check && pnpm type-check && pnpm test:coverage && pnpm check:licenses && pnpm build-only && pnpm size
```

```bash
cd docs && pnpm build
```

`pnpm lint:fix` und `pnpm format` beheben, was sie können.

## Was sie sicherstellen

- **Coverage:** mindestens 90 % im Backend (`fail_under` in `pyproject.toml`); im Frontend
  eine Untergrenze auf dem heutigen Stand (`vitest.config.ts`, etwa 88 % der Zeilen;
  heben Sie sie an, wenn Tests hinzukommen).
- **Lizenzen:** kein GPL, AGPL oder SSPL in Produktionsabhängigkeiten
  (`backend/scripts/check_licenses.py`, `frontend/scripts/check-licenses.mjs`).
- **Ungenutzter Code:** `pnpm lint` enthält knip (ungenutzte Dateien, Exporte und
  Abhängigkeiten; `knip.jsonc`).
- **Bundle-Größe:** Das gebaute Bundle muss im Budget aus `package.json` bleiben
  (`size-limit`; heben Sie es bewusst an, wenn eine Funktion es erfordert).
- **Generierte Dateien:** Migrationen, `frontend/openapi.json` und
  `frontend/src/api/schema.d.ts` müssen zum Code passen.

Die CI führt zusätzlich `manage.py check --deploy` mit Produktionseinstellungen aus (HSTS
und die HTTPS-Weiterleitung bleiben dem TLS-Proxy überlassen und sind in `settings.py`
stummgeschaltet) sowie Trivy: Secrets, behebbare kritische Schwachstellen und
Fehlkonfigurationen im Dockerfile lassen den Build fehlschlagen, sowohl im Repository als
auch im gebauten Image; Schwachstellen der Stufe HIGH werden gemeldet.

## Vor jedem Commit

Schnelle Prüfungen (ruff, prettier, oxlint, Leerzeichen) mit
[pre-commit](https://pre-commit.com), einmalig installiert:

```bash
uv tool run pre-commit install
```

## Backend-Tests

Die Backend-Tests laufen parallel (pytest-xdist, bis zu 8 Worker). Für eine einzelne Datei
oder einen einzelnen Test überspringt `-n0` den Start der Worker:

```bash
uv run pytest -n0 apps/accounts/tests/test_roles.py
```
