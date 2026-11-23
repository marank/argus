# Checks and tests

`just check` (VS Code task **Check: all**) runs the same checks as CI and must pass
before a push. The commands live in the `justfile`; CI calls the same recipes, one per job:

| Recipe | Checks |
| --- | --- |
| `just check-backend` | ruff, mypy, deptry, import layers, licenses, migrations, Django checks, translations, OpenAPI schema, tests |
| `just check-deploy` | `manage.py check --deploy` with production settings (`backend/deploy-check.env`) |
| `just check-frontend` | prettier, oxlint, ESLint, knip, types, tests, API types, licenses, build, bundle size |
| `just check-docs` | the documentation build |
| `just check-workflows` | the GitHub workflows (actionlint, zizmor) |

`just check-eol` is not part of `just check`: it asks endoflife.date when Python, Debian,
Node.js, PostgreSQL and Django in the versions Argus uses stop getting security fixes, and
fails 180 days before (`backend/scripts/check_eol.py`). CI runs it in the weekly build.

`just fix` formats and fixes what the tools can.

## What they enforce

- **No silenced checks:** every `# noqa`, `# type: ignore[…]` and `eslint-disable` names its
  rules and says why; unused ones fail.
- **Test order:** pytest-randomly shuffles the backend tests on every run, so a test that
  depends on another one fails. `uv run pytest --randomly-seed=last` repeats the last order.
- **Coverage:** at least 90 % in the backend (`fail_under` in `pyproject.toml`); a floor at
  today's level in the frontend (`vitest.config.ts`, about 88 % of lines; raise it as
  tests are added).
- **Licenses:** production dependencies must be compatible with AGPL-3.0-or-later.
  Permissive licenses, LGPL, GPL-3.0 and AGPL-3.0 are fine; GPL-2.0-only, a GPL without
  a version and SSPL are not (`backend/scripts/check_licenses.py`,
  `frontend/scripts/check-licenses.mjs`; exceptions checked by hand go into `ALLOW`).
- **Unused code:** `pnpm lint` includes knip (unused files, exports and dependencies;
  `knip.jsonc`).
- **Bundle size:** the built bundle must stay within the budget in `package.json`
  (`size-limit`; raise it deliberately when a feature needs it).
- **Generated files:** migrations, `frontend/openapi.json` and `frontend/src/api/schema.d.ts`
  must match the code.
- **Readability:** limits on tangle, not on length. Cyclomatic complexity at most 15
  (ruff `C90`, ESLint `complexity`, where a `switch` counts once) and nesting depth at most
  4 in the frontend. A function above the limit gets a `noqa` or `eslint-disable` comment
  with its reason, or is split.
- **Layers:** in every backend app `api` may import `services` and `models`, `services` may
  import `models`, never the other way round; `core`'s models import no other app
  (import-linter, contracts in `pyproject.toml`). In the frontend only `src/api/` uses the
  HTTP client, shared components and composables never import a view, and `src/utils/`
  stays pure (ESLint `no-restricted-imports`).
- **Translations:** no untranslated or fuzzy entry in `backend/locale/de`, and `django.mo`
  matches `django.po` (`backend/scripts/check_translations.py`).

`check --deploy` runs with production settings; HSTS and the https redirect are left to
the TLS proxy and silenced in `settings.py`. CI additionally runs Trivy:
secrets, fixable critical vulnerabilities and Dockerfile misconfigurations fail the
build, both in the repository and in the built image; HIGH vulnerabilities are reported.

## Before every commit

Fast checks (ruff, prettier, oxlint, whitespace) with [pre-commit](https://pre-commit.com),
installed once:

```bash
uv tool run pre-commit install
```

## Backend tests

The backend tests run in parallel (pytest-xdist, up to 8 workers) with
`config/settings_test.py`, so variables in the environment do not change them. For a
single file or test, `-n0` skips the worker start-up:

```bash
just test-backend -n0 apps/accounts/tests/test_roles.py
```

::: info Good to know
Without the gettext tools (usual on Windows) the translation check only checks the
committed `.po` file and warns that new strings in the code are not covered; CI has them.
On Windows: `winget install mlocati.GetText`.
:::
