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
(shared pickup terminal). It also creates about 25 more employees (e.g. `jkoch`
in IT), a second site, some 150 devices with history, requests in every step,
purchase orders, licenses and problem reports.

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
| `LDAP_*` | Optional LDAP / AD login, see [LDAP login](#ldap-login). |

The app container runs unprivileged with a read-only root filesystem; health
checks use `/api/health`. Behind a TLS proxy, forward `X-Forwarded-Proto` and list
the `https://` URL in `APP_URLS`.

## LDAP login

Employees can sign in with their directory account (LDAP or Active Directory).
Configure it in the app under *Administration → LDAP login* (superusers only; also
in the Django admin) or with environment variables, one per setting
(`LDAP_SERVER_URI`, `LDAP_BIND_DN`, `LDAP_ATTR_EMPLOYEE_NUMBER`, … – see
`.env.example`). A non-empty variable wins over the in-app value, which is then shown
read-only.

- Login: local accounts are checked first (administrator, pickup terminal), then the
  directory: search with the service account (`LDAP_BIND_DN`, or anonymously), bind as
  the found entry with the entered password.
- Attribute mapping: first name, last name, employee number, email, job title and
  phone each name an LDAP attribute (defaults: `givenName`, `sn`, `employeeID`,
  `mail`, `title`, `telephoneNumber`). They are overwritten at every login; leave a
  mapping empty to maintain that field in Argus instead.
- Users are created on first login (unless disabled) or linked to an existing Argus
  user of the same name. Local superusers are never taken over by a directory account.
- *Test connection* on the settings page checks the unsaved configuration and shows
  the values a given user would receive.
- Several servers (comma separated) are tried in order. For an internal CA, mount the
  PEM file into the container and set `LDAP_CA_CERT_FILE`.

## Two-factor sign-in

Every user (local or LDAP) can switch on a second sign-in step under
*user menu → Sign-in & security*:

- **Authenticator app** (TOTP, RFC 6238: 6 digits, 30 s) – set up by scanning a QR
  code; a code is accepted only once.
- **Code by email** – a 6-digit code valid for 10 minutes; offered only when the user
  has an email address and mail sending is configured.
- **Backup codes** – ten one-time codes shown once at setup (copy or save as text
  file) and renewable at any time; only salted hashes are stored.

Setting up, renewing codes and switching off need the password. After five wrong
codes the password has to be entered again. IT resets the second step of a user who
lost phone and codes in the employee drawer (*Master data → Employees*) or with the
Django admin action; only administrators can reset administrators. The Django admin
signs in through the app's login, so the second step applies there too.

## Features

- **Inventory** – individually tracked devices (laptops, phones, headsets, MDEs, …)
  with serial number, IMEI, MAC, location, assignment and a full life cycle log
  (battery replacements, repairs, hand-outs, …). Consumables such as ink cartridges
  are tracked by quantity per location with minimum quantities and movements, and
  can be assigned to device models (compatible with) or to individual devices.
- **Software licenses** – categories are either hardware or software. Licenses of
  software products have seats, a term and are assigned to employees or devices;
  employees can request software in the portal, IT then assigns a license.
- **Email notifications** – via SMTP, configured under Settings → Email: new
  requests and problem reports for IT, confirmations, pickups and return reminders
  for employees, license expiry. Administrators switch kinds on and off site-wide,
  every user can opt out under Notifications. Time-based reminders come from
  `python manage.py send_reminders`, which the Docker image runs every hour.
- **Site settings** – modules and features can be switched off; deadlines such as
  the default and maximum loan period and warning periods are configurable.
- **Scanning** – keyboard-wedge barcode scanners work anywhere in the IT views:
  inventory number, serial, IMEI or EAN jump straight to the device or model.
  Several devices can be scanned in at once.
- **Number sequences** – configurable patterns per category
  (`{prefix}{year}-{seq}`, yearly/monthly restart) for inventory, reservation and
  order numbers.
- **Self-service portal** – employees request devices by group ("any headset") or
  model, for a period or permanently, and follow status, pickup time and their
  assigned devices. Consumables that fit their own devices are offered as a quick pick.
- **Department approval** – categories can require approval (inherited by
  subcategories). Such requests wait as *awaiting approval* until an approver of the
  requester's department approves them under *Approvals* in the portal; only then
  does IT get them. Requests go straight to IT for exempt employees, when IT records
  them on someone's behalf, when the department has no approvers, and approvers'
  own requests count as approved.
- **Reservation workflow** – IT confirms (optionally with reduced quantities),
  sets pickup date and place, allocates concrete devices (scan, pick or automatic),
  marks the request ready, hands out and takes back.
- **Pickup terminal & handover record** – when a request is ready, IT chooses
  *pickup at terminal* or *delivered by IT*. A shared touch PC signed in with a
  terminal account (`is_terminal`) lists prepared pickups only; the collecting
  person checks the devices, adds notes (e.g. damage), is recorded (requester or
  a colleague) and signs on screen. Direct and delivered hand-outs are recorded
  by IT without a signature. Every handover has a printable record.
- **Procurement** – demand from requests the pool cannot cover and consumables below
  minimum turns into purchase orders; goods receipt creates devices (with scanned
  serials) or books consumables, and directly allocates them to the waiting request.
- **Master data** – manufacturers, suppliers, categories, models, locations,
  departments, employees and number sequences.

## Project layout

```
backend/
  config/            settings, URLs, API assembly (config/api.py)
  apps/
    core/            base models, number sequences, auth/session API, CRUD helpers
    accounts/        users, departments, teams, LDAP and two-factor sign-in
    masterdata/      manufacturers, suppliers, categories, models, locations
    inventory/       assets, asset events, consumables and their movements
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
