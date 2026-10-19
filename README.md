# Argus

IT asset management for the IT department: inventory, employee reservations,
device preparation and procurement.

| Part     | Stack                                                           |
| -------- | --------------------------------------------------------------- |
| Backend  | Python 3.14 · Django 6.1 · django-ninja (REST) · managed by `uv` |
| Frontend | Vue 3.5 · TypeScript · Vite · Naive UI · Pinia · vue-i18n · `pnpm` |

Code and data are English; German ships as translation (backend `locale/`,
frontend `src/i18n/locales/de`).

## Quick start

```bash
# Backend
cd backend
uv sync
uv run python manage.py migrate
uv run python manage.py seed_demo      # optional demo data
uv run python manage.py runserver

# Frontend (second terminal)
cd frontend
pnpm install
pnpm dev                               # http://localhost:5173, proxies /api to :8000
```

If the backend runs elsewhere, set `BACKEND_URL` (e.g.
`BACKEND_URL=http://127.0.0.1:8010 pnpm dev`). Local development needs no
`.env`: without variables Django runs with debug on and SQLite.

VS Code: *Terminal → Run Task…* offers all of this as tasks (`.vscode/tasks.json`),
e.g. **Dev: start all**, **Check: all**, **DB: seed demo data**, **Docker: build and start**.

Demo accounts created by `seed_demo` (development only, password `argus-demo`):
`admin` (superuser), `it` (IT department), `employee`, `sales`, `terminal`
(shared pickup terminal).

## Docker

One image runs nginx (serves the built frontend, proxies `/api` and `/admin`),
gunicorn (Django) and supervisord; docker compose adds PostgreSQL.

```bash
cp .env.example .env      # set APP_URLS, SECRET_KEY, ADMIN_PASSWORD, POSTGRES_PASSWORD
docker compose up --build -d
```

Argus is then available on `http://localhost:8080`, the Django admin on `/admin/`
(user from `ADMIN_USERNAME` / `ADMIN_PASSWORD`, created on first start). On every
start the container waits for the database and applies migrations.

| Variable | Purpose |
| --- | --- |
| `APP_URLS` | All URLs users open Argus under, comma separated. Allowed hosts, CSRF/CORS origins and secure cookies (all `https`) are derived from it. |
| `APP_PORT` | Host port (default `8080`). |
| `APP_WORKERS` | Gunicorn workers (default 2 × CPU + 1, max 5). |
| `APP_DEMO_DATA` | `true` seeds an empty database with demo data. |
| `SECRET_KEY` | Django secret key (required). |
| `TIME_ZONE`, `LOG_LEVEL` | Defaults `Europe/Berlin`, `INFO`. |
| `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` | First administrator. |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Database (also used by the Postgres container). |

The app container runs unprivileged with a read-only root filesystem; health
checks use `/api/health`. Behind a TLS proxy, forward `X-Forwarded-Proto` and list
the `https://` URL in `APP_URLS`.

## Features

- **Inventory** – individually tracked devices (laptops, phones, headsets, MDEs, …)
  with serial number, IMEI, MAC, location, assignment and a full life cycle log
  (battery replacements, repairs, hand-outs, …). Bulk items such as ink cartridges
  are tracked as stock with minimum quantities and movements.
- **Scanning** – keyboard-wedge barcode scanners work anywhere in the IT views:
  inventory number, serial, IMEI or EAN jump straight to the device or model.
  Several devices can be scanned in at once.
- **Number sequences** – configurable patterns per device group
  (`{prefix}{year}-{seq}`, yearly/monthly restart) for inventory, reservation and
  order numbers.
- **Self-service portal** – employees request devices by group ("any headset") or
  model, for a period or permanently, and follow status, pickup time and their
  assigned devices.
- **Reservation workflow** – IT approves (optionally with reduced quantities),
  sets pickup date and place, allocates concrete devices (scan, pick or automatic),
  marks the request ready, hands out and takes back.
- **Pickup terminal & handover record** – when a request is ready, IT chooses
  *pickup at terminal* or *delivered by IT*. A shared touch PC signed in with a
  terminal account (`is_terminal`) lists prepared pickups only; the collecting
  person checks the devices, adds notes (e.g. damage), is recorded (requester or
  a colleague) and signs on screen. Direct and delivered hand-outs are recorded
  by IT without a signature. Every handover has a printable record.
- **Procurement** – demand from requests the pool cannot cover and stock below
  minimum turns into purchase orders; goods receipt creates devices (with scanned
  serials) or books stock, and directly allocates them to the waiting request.
- **Master data** – manufacturers, suppliers, device groups, models, locations,
  departments, employees and number sequences.

## Project layout

```
backend/
  config/            settings, URLs, API assembly (config/api.py)
  apps/
    core/            base models, number sequences, auth/session API, CRUD helpers
    accounts/        users and departments
    masterdata/      manufacturers, suppliers, categories, models, locations
    inventory/       assets, asset events, stock items and movements
    reservations/    reservations, items, allocations, workflow, employee portal
    procurement/     purchase orders, demand calculation, goods receipt
    dashboard/       overview figures
  Each app: models/, schemas/, api/, services/, admin/ – one file per concept.
  locale/            German translations

frontend/src/
  api/               typed API clients per domain
  types/             TypeScript types per domain
  components/        layout, common, crud, inventory, reservations, procurement
  views/             pages per area (portal, inventory, reservations, …)
  composables/       list state, actions, formatting, scanner, confirm
  i18n/locales/      en/ and de/, one file per area
  theme/             palette and Naive UI overrides (light/dark)
```

All models use random UUIDs as primary keys (`apps.core.models.UUIDModel`, also on
`accounts.User`); URLs and API payloads carry these UUIDs.

Business rules live in `services/` (e.g. `apps/reservations/services/workflow.py`);
API modules stay thin.

## Checks

```bash
cd backend && uv run pytest && uv run ruff check .
cd frontend && pnpm type-check && pnpm lint && pnpm test:unit --run
```

## Translations

```bash
cd backend
uv run python manage.py makemessages -l de --ignore ".venv/*"
# edit locale/de/LC_MESSAGES/django.po
uv run python manage.py compilemessages
```
