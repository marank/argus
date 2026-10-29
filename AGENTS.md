# Argus — conventions for contributors and coding agents

IT asset management. Django backend (`backend/`, API via Django Ninja), Vue 3 +
TypeScript SPA (`frontend/`, Naive UI), one hardened Docker image. Read this before
changing structure; `README.md` has setup, commands and the glossary of domain terms.

## Commands

VS Code tasks (`.vscode/tasks.json`) hold the everyday commands; the README lists the plain equivalents.
- **Dev: start all**: Django :8000 + Vite :5173 → http://localhost:5173. `seed_demo` fills the database.
- **Check: all** runs everything CI runs and must pass before a push. If you change a check, change it in
  both `tasks.json` and `.gitea/workflows/build.yaml`.
- **DB: make migrations** after model changes; commit the migrations (CI fails on missing ones).
- Frontend package manager is **pnpm** only. Backend dependencies via `uv add` / `uv add --dev`.

## Backend rules

- Apps live in `backend/apps/<name>/`, registered in `INSTALLED_APPS`.
- **No monolithic modules.** `models/`, `admin/`, `api/`, `schemas/`, `services/`, `tests/` are packages
  with one file per model/resource; `__init__.py` re-exports explicitly. Relations use string
  references (`"app.Model"`).
- **Every model inherits `apps.core.models.UUIDModel` or `TimeStampedModel`** (UUIDv7 primary key);
  `manage.py check` fails (`core.E001`) otherwise. URLs and payloads carry these UUIDs. Order
  queries explicitly.
- Business rules go in `services/`, not in API modules or a model's `save()`.
- API: under `/api/`, no trailing slashes, session auth + CSRF, UUIDs in paths. `/api/health` stays
  unauthenticated and exactly at that path (container health check, CI smoke test).
- Configuration only via environment variables (`config/env.py` helpers); every new variable gets a
  commented entry in `.env.example` and a row in the README table.
- User-facing strings in English, wrapped in `gettext`; German goes into `backend/locale/de`.
- mypy (`[tool.mypy]` in `pyproject.toml`) must pass; annotate new code. Endpoints behind auth take
  `request: AuthedRequest` (`apps/core/api/security.py`), so `request.user` is a `User`.
  `# type: ignore` only with an error code and a reason.
- Backend coverage must stay ≥ 90 %. No GPL/AGPL/SSPL dependencies (CI license check).

## Frontend rules

- API calls through the per-domain modules in `src/api/`, types in `src/types/`; views per area in
  `src/views/`, shared pieces in `src/components/` and `src/composables/`.
- UI from Naive UI, themed in `src/theme/`. Every visible text goes through vue-i18n
  (`src/i18n/locales/en` and `de`, one file per area).
- No inline `<script>` and no remote scripts or fonts: the CSP only allows our own origin.

## Docker / runtime

- The app container runs read-only, without capabilities, as an unprivileged user. Only `/tmp` is
  writable; new features must not loosen the hardening.
- supervisord runs gunicorn, uvicorn (`/api/events`), the Procrastinate worker and nginx; nginx serves
  the SPA, `/django-static/`, and proxies `/api` and `/admin`.
- The `backup` service dumps the database nightly; see README "Backups".
