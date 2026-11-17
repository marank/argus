# Argus — conventions for contributors and coding agents

IT asset management. Django backend (`backend/`, API via Django Ninja), Vue 3 +
TypeScript SPA (`frontend/`, Naive UI), one hardened Docker image. Read this before
changing structure; `README.md` has setup, commands and the glossary of domain terms.

## Commands

VS Code tasks (`.vscode/tasks.json`) hold the everyday commands; the README lists the plain equivalents.
- **Dev: start all**: Django :8000 + Vite :5173 → http://localhost:5173. `seed_demo` fills the database.
- **Check: all** runs everything CI runs and must pass before a push. If you change a check, change it in
  both `tasks.json` and `.github/workflows/build.yaml`.
- **DB: make migrations** after model changes; commit the migrations (CI fails on missing ones).
- **API: update types** after any API change: exports `frontend/openapi.json` and regenerates
  `frontend/src/api/schema.d.ts`; commit both (CI fails when they are out of date).
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
- mypy runs in strict mode (`[tool.mypy]` in `pyproject.toml`; tests need no annotations) and must
  pass: annotate all new code. Admin classes take their model (`admin.ModelAdmin[Asset]`; made
  subscriptable at runtime in settings). Endpoints behind auth take
  `request: AuthedRequest` (`apps/core/api/security.py`), so `request.user` is a `User`.
  `# type: ignore` only with an error code and a reason.
- Backend coverage must stay ≥ 90 %. No GPL/AGPL/SSPL dependencies (CI license check).

## Frontend rules

- API calls through the per-domain modules in `src/api/`; views per area in `src/views/`, shared
  pieces in `src/components/` and `src/composables/`.
- Types of API payloads in `src/types/` are aliases of the generated schema types
  (`Schemas['AssetOut']` from `src/api/types.ts`), never hand-written copies. Never edit
  `src/api/schema.d.ts`.
- A list of every value of an API enum is written with `allValues<Schemas['AssetStatus']>({ … })`
  (`src/utils/enums.ts`), so a value added in the backend fails the type check until it is listed.
- UI from Naive UI, themed in `src/theme/`. Every visible text goes through vue-i18n
  (`src/i18n/locales/en` and `de`, one file per area).
- No inline `<script>` and no remote scripts or fonts: the CSP only allows our own origin.

## Documentation

- `docs/` holds the user and operator documentation (VitePress), served at `/docs/`. A change users
  or operators notice (new feature, changed rule, new setting or variable) updates the matching page.
- Content in German, file and folder names in English. Professional and direct: no filler, no
  unnecessary detail. Use the exact UI labels from `frontend/src/i18n/locales/de`; edge cases go
  into `::: info Gut zu wissen` boxes on the feature's page.
- Three areas: `employees/`, `approvers/` (linkable for everyone, never link into `it/`) and `it/`
  (IT work, `administration/`, `operations/`). Each area has its own sidebar in `.vitepress/config.mts`.
- `pnpm build` in `docs/` must pass (dead links, anchors and IT links in the open areas fail it).

## Docker / runtime

- The app container runs read-only, without capabilities, as an unprivileged user. Only `/tmp` is
  writable; new features must not loosen the hardening.
- supervisord runs gunicorn, uvicorn (`/api/events`), the Procrastinate worker and nginx; nginx serves
  the SPA, `/django-static/`, and proxies `/api` and `/admin`.
- The job worker dumps the database nightly into the `db-backups` volume (`/backups`,
  `apps/core/services/backups.py`); see README "Backups". `compose.yml` must work with
  `.env` alone, without any other file from the repository.
