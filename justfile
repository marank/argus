# Argus commands: the one place they live. CI (.github/workflows/build.yaml) and the VS Code
# tasks (.vscode/tasks.json) call these recipes, so a check is changed here and nowhere else.
# `just` lists them. Needs just >= 1.38: `uv tool install rust-just` or `winget install Casey.Just`.

set windows-shell := ["powershell.exe", "-NoLogo", "-NoProfile", "-Command"]

# Not seen by Dependabot: update by hand now and then (PyPI: actionlint-py, zizmor).
actionlint := "1.7.12.25"
zizmor := "1.32.0"

# List the recipes
default:
    @just --list

# --- Setup --------------------------------------------------------------------------

# Install all dependencies
setup: setup-backend setup-frontend setup-docs

[working-directory: 'backend']
setup-backend:
    uv sync

[working-directory: 'frontend']
setup-frontend:
    pnpm install

[working-directory: 'docs']
setup-docs:
    pnpm install

# --- Development ----------------------------------------------------------------------

# Django on :8000 (SQLite in backend/, no job worker)
[working-directory: 'backend']
dev-backend:
    uv run python manage.py runserver 127.0.0.1:8000

# Vite on :5173, proxying /api, /admin, /django-static and /docs
[working-directory: 'frontend']
dev-frontend:
    pnpm dev

# VitePress on :5175/docs/
[working-directory: 'docs']
dev-docs:
    pnpm dev --port 5175

# Optional PostgreSQL like CI (compose.dev.yml); then run the backend with DB_HOST=localhost
db-up:
    docker compose -f compose.dev.yml up -d

[working-directory: 'backend']
migrate:
    uv run python manage.py migrate

# After model changes; commit the migrations
[working-directory: 'backend']
migrations:
    uv run python manage.py makemigrations --no-header

# Demo users (password argus-demo), devices and requests
[working-directory: 'backend']
seed:
    uv run python manage.py seed_demo

# Delete all data, then seed the demo data again
[confirm('Delete all data in the local database?')]
[working-directory: 'backend']
reset:
    uv run python manage.py flush --no-input
    uv run python manage.py seed_demo

[working-directory: 'backend']
superuser:
    uv run python manage.py createsuperuser

# After API changes: frontend/openapi.json -> src/api/schema.d.ts; commit both
[working-directory: 'frontend']
api-types: api-schema
    pnpm api:types

[working-directory: 'backend']
api-schema:
    uv run python manage.py export_openapi ../frontend/openapi.json

# After new backend texts (needs gettext); then translate backend/locale/de/LC_MESSAGES/django.po
[working-directory: 'backend']
messages:
    uv run python manage.py makemessages -l de --ignore '.venv/*' --no-wrap

# django.po -> django.mo (needs gettext); commit both
[working-directory: 'backend']
compile-messages:
    uv run python manage.py compilemessages --ignore '.venv/*'

# --- Fixes and tests ------------------------------------------------------------------

# Format and auto-fix backend and frontend
fix: fix-backend fix-frontend

[working-directory: 'backend']
fix-backend:
    uv run ruff format .
    uv run ruff check --fix .

[working-directory: 'frontend']
fix-frontend:
    pnpm format
    pnpm lint:fix

[working-directory: 'backend']
test-backend *args:
    uv run pytest {{args}}

[working-directory: 'frontend']
test-frontend *args:
    pnpm exec vitest run {{args}}

# --- Checks (= CI) --------------------------------------------------------------------

# Everything CI checks; must pass before a push
check: check-backend check-deploy check-frontend check-docs check-workflows

# ruff, mypy, deptry, import layers, licenses, migrations, Django checks, translations, OpenAPI, tests
[working-directory: 'backend']
check-backend:
    uv sync --locked
    uv run ruff check --output-format=concise .
    uv run ruff format --check .
    uv run mypy .
    uv run deptry .
    uv run lint-imports
    uv run python scripts/check_licenses.py
    uv run python manage.py makemigrations --check --dry-run
    uv run python manage.py check --fail-level WARNING
    uv run --with polib python scripts/check_translations.py
    uv run python scripts/check_openapi.py
    uv run pytest -q --cov

# Django's deploy checks with production settings behind a TLS proxy (deploy-check.env)
[working-directory: 'backend']
check-deploy:
    uv run --env-file deploy-check.env python manage.py check --deploy --fail-level WARNING

# prettier, oxlint, eslint, knip, types, tests, API types, licenses, build, bundle size
[working-directory: 'frontend']
check-frontend:
    pnpm install --frozen-lockfile
    pnpm check
    pnpm api:types
    git diff --exit-code -- src/api/schema.d.ts
    pnpm check:licenses
    pnpm build-only
    pnpm size

# VitePress build: dead links, anchors, IT links in the open areas, missing translations
[working-directory: 'docs']
check-docs:
    pnpm install --frozen-lockfile
    pnpm build

# GitHub workflows: syntax (actionlint) and security (zizmor)
check-workflows:
    uvx --from actionlint-py=={{actionlint}} actionlint
    uvx zizmor@{{zizmor}} .github/

# --- Docker ----------------------------------------------------------------------------

# Build the image locally and start it with .env (http://127.0.0.1:8080)
docker-up $ARGUS_IMAGE="argus:latest":
    docker build -t {{ARGUS_IMAGE}} .
    docker compose up -d

# Dump the database into the backups volume now (it is also dumped nightly)
docker-backup:
    docker compose exec app python manage.py backup_database

docker-logs:
    docker compose logs -f app

docker-down:
    docker compose down
