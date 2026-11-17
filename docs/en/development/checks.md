# Checks and tests

The VS Code task **Check: all** runs the same checks as CI and must pass before a push.
By hand:

```bash
cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy . && uv run deptry . && uv run pytest --cov
```

```bash
cd frontend && pnpm lint && pnpm format:check && pnpm type-check && pnpm test:coverage && pnpm check:licenses && pnpm build-only && pnpm size
```

```bash
cd docs && pnpm build
```

`pnpm lint:fix` and `pnpm format` fix what they can.

## What they enforce

- **Coverage:** at least 90 % in the backend (`fail_under` in `pyproject.toml`); a floor at
  today's level in the frontend (`vitest.config.ts`, about 88 % of lines; raise it as
  tests are added).
- **Licenses:** no GPL, AGPL or SSPL in production dependencies
  (`backend/scripts/check_licenses.py`, `frontend/scripts/check-licenses.mjs`).
- **Unused code:** `pnpm lint` includes knip (unused files, exports and dependencies;
  `knip.jsonc`).
- **Bundle size:** the built bundle must stay within the budget in `package.json`
  (`size-limit`; raise it deliberately when a feature needs it).
- **Generated files:** migrations, `frontend/openapi.json` and `frontend/src/api/schema.d.ts`
  must match the code.

CI additionally runs `manage.py check --deploy` with production settings (HSTS and the
https redirect are left to the TLS proxy and silenced in `settings.py`) and Trivy:
secrets, fixable critical vulnerabilities and Dockerfile misconfigurations fail the
build, both in the repository and in the built image; HIGH vulnerabilities are reported.

## Before every commit

Fast checks (ruff, prettier, oxlint, whitespace) with [pre-commit](https://pre-commit.com),
installed once:

```bash
uv tool run pre-commit install
```

## Backend tests

The backend tests run in parallel (pytest-xdist, up to 8 workers). For a single file or
test, `-n0` skips the worker start-up:

```bash
uv run pytest -n0 apps/accounts/tests/test_roles.py
```
