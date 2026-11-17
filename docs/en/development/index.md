# Development setup

Argus is a Django backend (`backend/`, REST API with Django Ninja) and a Vue 3 +
TypeScript single-page app (`frontend/`, Naive UI), shipped as one Docker image. The
conventions every change follows are in
[AGENTS.md](https://github.com/marank/argus/blob/main/AGENTS.md); how to propose a change
is in [CONTRIBUTING.md](https://github.com/marank/argus/blob/main/CONTRIBUTING.md).

| Part     | Stack                                                              |
| -------- | ------------------------------------------------------------------ |
| Backend  | Python 3.14 · Django 6.1 · Django Ninja · managed by `uv`          |
| Frontend | Vue 3.5 · TypeScript · Vite · Naive UI · Pinia · vue-i18n · `pnpm` |
| Docs     | VitePress (this site), `pnpm`                                      |

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (installs the right Python itself)
- Node.js 22.18+ or 24.12+ and [pnpm](https://pnpm.io/)
- Docker, only for PostgreSQL and for building the image

## Run it locally

```bash
cd backend
uv sync
uv run python manage.py migrate
uv run python manage.py seed_demo      # optional demo data
uv run python manage.py runserver
```

In a second terminal:

```bash
cd frontend
pnpm install
pnpm dev                               # http://localhost:5173, proxies /api to :8000
```

Local development needs no `.env`: without `SECRET_KEY` Django runs with debug on and a
SQLite file (`backend/db.sqlite3`). If the backend runs on another address, set
`BACKEND_URL`, e.g. `BACKEND_URL=http://127.0.0.1:8010 pnpm dev`.

### With PostgreSQL

SQLite is enough for most work. The job queue and live updates need PostgreSQL: start
one with `docker compose -f compose.dev.yml up -d` and run the backend with
`DB_HOST=localhost`. Without PostgreSQL, jobs (e.g. mails) run right after the request
and pages do not update by themselves.

## VS Code tasks

*Terminal → Run Task…* offers everything as tasks (`.vscode/tasks.json`), among them:

| Task | What it does |
| --- | --- |
| **Dev: start all** | Django on :8000 and Vite on :5173 |
| **DB: start dev postgres** | PostgreSQL from `compose.dev.yml` |
| **DB: seed demo data** | `seed_demo` |
| **DB: make migrations** | after model changes |
| **API: update types** | after API changes, see [API types and translations](./api-and-translations) |
| **Check: all** | everything CI runs, see [Checks and tests](./checks) |
| **Docker: build and start** | builds the image and starts it with `compose.yml` |

## Demo data

`seed_demo` fills an empty database. All demo accounts have the password `argus-demo`:

| User | Role |
| --- | --- |
| `admin` | superuser |
| `it` | IT department |
| `employee`, `sales` | employees |
| `terminal` | shared pickup terminal |

It also creates about 25 more employees (e.g. `jkoch` in IT), a second site, some
150 devices with history, requests in every step, purchase orders, licenses and problem
reports.

## Next

- [Architecture](./architecture): layout, conventions and the domain terms
- [Checks and tests](./checks): what has to pass before a push
- [API types and translations](./api-and-translations)
- [Writing documentation](./documentation)
- [CI and releases](./ci)
