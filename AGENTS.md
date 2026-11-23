# Argus — conventions for contributors and coding agents

IT asset management. Django backend (`backend/`, API via Django Ninja), Vue 3 +
TypeScript SPA (`frontend/`, Naive UI), one hardened Docker image. Read this before
changing structure; `docs/en/development/` has setup, commands and the glossary of domain terms.

## Commands

Every command lives in the `justfile` (`just` lists them; `uv tool install rust-just`). The VS Code
tasks (`.vscode/tasks.json`) and CI only call its recipes, so a check is changed there and nowhere else.
- **Dev: start all** / `just dev-backend` + `just dev-frontend`: Django :8000 + Vite :5173 →
  http://localhost:5173. `just seed` fills the database.
- **Check: all** / `just check` runs everything CI runs and must pass before a push.
  `just check-eol` (weekly in CI, not in `check`) fails 180 days before Python, Debian, Node.js,
  PostgreSQL or Django lose security support: that is how ignored majors come up.
- **DB: make migrations** / `just migrations` after model changes; commit the migrations (CI fails on
  missing ones).
- **API: update types** / `just api-types` after any API change: exports `frontend/openapi.json` and
  regenerates `frontend/src/api/schema.d.ts`; commit both (CI fails when they are out of date).
- Actions are pinned to commit SHAs, images in the Dockerfile and CI to tag + digest; compose files
  name images by tag only, as operators expect. Dependabot moves them. Not seen by
  Dependabot: `TRIVY_IMAGE`, `POSTGRES_IMAGE` (same major as `compose.yml`), `JUST_VERSION` and the job
  containers in `build.yaml`; `actionlint`/`zizmor` in the `justfile`; `SUPERVISOR_VERSION` in the
  Dockerfile; pre-commit hooks.
- Commit messages and pull request titles are **Conventional Commits** (`feat:`, `fix:`, `docs:`,
  `refactor:`, `test:`, `build:`, `ci:`, `chore:`; `!` for breaking changes; `deps:` for runtime
  dependency updates, listed under "Dependencies"): release-please
  (`.github/workflows/release.yaml`) makes the version and `CHANGELOG.md` from them, and pull
  requests are squash-merged with their title. Never edit `CHANGELOG.md` or the release-please
  manifest by hand.
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
- Layers per app: `api` → `services` → `models`, never back; `core`'s models import no other app
  (import-linter in `pyproject.toml`; a new app is added to its contracts, a test checks that).
- Complexity ≤ 15 per function (ruff `C90`, ESLint `complexity`), no length limits; above it, split
  or add `noqa`/`eslint-disable` with the reason. Tests use `config/settings_test.py`.
- API: under `/api/`, no trailing slashes, session auth + CSRF, UUIDs in paths. `/api/health` stays
  unauthenticated and exactly at that path (container health check, CI smoke test).
- Configuration only via environment variables (`config/env.py` helpers); every new variable gets a
  commented entry in `.env.example` and a row in `docs/{de,en}/it/operations/configuration.md`.
- User-facing strings in English, wrapped in `gettext`; German goes into `backend/locale/de`.
- mypy runs in strict mode (`[tool.mypy]` in `pyproject.toml`; tests need no annotations) and must
  pass: annotate all new code. Admin classes take their model (`admin.ModelAdmin[Asset]`; made
  subscriptable at runtime in settings). Endpoints behind auth take
  `request: AuthedRequest` (`apps/core/api/security.py`), so `request.user` is a `User`.
  `# type: ignore` only with an error code and a reason.
- Backend coverage must stay ≥ 90 %. Production dependencies must be compatible with
  AGPL-3.0-or-later: no GPL-2.0-only or SSPL (CI license check).

## Frontend rules

- API calls through the per-domain modules in `src/api/` (only they use the HTTP client; `src/utils/`
  stays pure, shared code never imports a view: ESLint `no-restricted-imports`); views per area in `src/views/`, shared
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

- `docs/` holds the documentation (VitePress), served at `/docs/`. A change users or operators
  notice (new feature, changed rule, new setting or variable) updates the matching page.
- **Every page exists in German and English** under the same path in `docs/de/` and `docs/en/`;
  change both in the same commit (the build fails when a counterpart is missing). New pages get a
  German and English title in `SIDEBARS` in `.vitepress/config.mts`.
- Professional and direct: no filler, no unnecessary detail. Use the exact UI labels from
  `frontend/src/i18n/locales/de` and `.../en`; edge cases go into `::: info Gut zu wissen` /
  `::: info Good to know` boxes on the feature's page. File and folder names in English.
- Four areas per language: `employees/`, `approvers/` (linkable for everyone, never link into
  `it/`), `it/` (IT work, `administration/`, `operations/`) and `development/` (contributors).
  Each has its own sidebar and search.
- `pnpm build` in `docs/` must pass (dead links, anchors, IT links in the open areas and missing
  translations fail it).

## Docker / runtime

- The app container runs read-only, without capabilities, as an unprivileged user. Only `/tmp` is
  writable; new features must not loosen the hardening.
- supervisord runs gunicorn, uvicorn (`/api/events`), the Procrastinate worker and nginx; nginx serves
  the SPA, `/django-static/`, and proxies `/api` and `/admin`.
- The job worker dumps the database nightly into the `db-backups` volume (`/backups`,
  `apps/core/services/backups.py`); see `docs/en/it/operations/backups.md`. `compose.yml` must work with
  `.env` alone, without any other file from the repository.

## House defaults

Checked against django-spa-defaults 1.8.0 (2026-11-23). Accepted deviations and settled judgements,
one line each as `- ID: decision and reason` (IDs from the project-defaults checklist); the review
does not report these again:

- Releases: release-please
- Contributions: team only
- BE-11: settled, passes: `DEBUG` defaults to false (only the justfile sets it for development),
  and without `DEBUG` the placeholder or a short `SECRET_KEY` stops the start (`config/settings.py`).
- FE-05: accepted for now: frontend coverage floor is 88/86/79/82 (lines/statements/functions/
  branches, `frontend/vitest.config.ts`); raise it with new tests until it reaches 90/90/85/85.
- BE-13: settled, passes: the sign-in code and the test mail are sent within the request on purpose,
  the user waits for them and must learn at once when they fail; the code must not end up in the
  job table (`accounts/services/two_factor.py`, `core/api/mail_settings.py`).
- BE-14: settled, passes: the remaining saves in API modules write only the endpoint's own object
  (settings singletons, preferences, the generic CRUD layer, a consumable's minimum) or only read
  (`requests/api/queries.py`); nothing else has to happen with them.
- FE-08: accepted for now: ESLint runs without type information; comes with typed linting
  (`recommendedTypeChecked`), the next step on the frontend lint.
- FE-10: accepted for now: comes with typed linting (see FE-08).
- FE-11: accepted for now: comes with typed linting (see FE-08).
- FE-12: accepted for now: comes with typed linting (see FE-08).
- FE-16: accepted for now: `strictTemplates` reports about 300 errors, mostly Naive UI typings
  (native attributes like `title` on components, union-typed `v-model`); fix them view by view.
- FE-14: accepted for now: eslint-plugin-vue at `essential`; raise to `strongly-recommended`
  together with FE-15.
- FE-15: accepted for now: `vue/no-unused-properties` comes with FE-14.
- FE-17: accepted for now: no accessibility linting yet; add eslint-plugin-vuejs-accessibility
  and fix its findings in the forms.
- BE-17: accepted for now: cognitive complexity is not limited yet (cyclomatic is, at 15); add
  complexipy and split what it reports.
- FE-09: accepted for now: as BE-17, with sonarjs `cognitive-complexity`.
- REPO-22: accepted for now: no duplicate-code check yet; add jscpd with a floor at today's share
  and lower it to 3 %.
- REPO-23: accepted for now: no lint hook for coding agents yet.
