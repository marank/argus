# Argus

IT asset management for the IT department: inventory, employee requests,
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

SQLite is enough for most work. The job queue and live updates need PostgreSQL;
for those, start one with `docker compose -f compose.dev.yml up -d` (VS Code task
**DB: start dev postgres**) and run the backend with `DB_HOST=localhost`.

If the backend runs elsewhere, set `BACKEND_URL` (e.g.
`BACKEND_URL=http://127.0.0.1:8010 pnpm dev`). Local development needs no
`.env`: without variables (no `SECRET_KEY`) Django runs with debug on and SQLite.

VS Code: *Terminal → Run Task…* offers all of this as tasks (`.vscode/tasks.json`),
e.g. **Dev: start all**, **Check: all** (same as CI), **DB: seed demo data**, **Docker: build and start**.

Demo accounts created by `seed_demo` (development only, password `argus-demo`):
`admin` (superuser), `it` (IT department), `employee`, `sales`, `terminal`
(shared pickup terminal). It also creates about 25 more employees (e.g. `jkoch`
in IT), a second site, some 150 devices with history, requests in every step,
purchase orders, licenses and problem reports.

## Docker

One image runs nginx (serves the built frontend, proxies `/api` and `/admin`),
gunicorn (Django), uvicorn for the live update stream (`/api/events`), the background
job worker and supervisord; docker compose adds PostgreSQL.

```bash
cp .env.example .env      # set APP_URLS, SECRET_KEY, ADMIN_PASSWORD, POSTGRES_PASSWORD
docker compose up --build -d
```

Argus is then available on `http://localhost:8080`, the Django admin on `/admin/`
(user from `ADMIN_USERNAME` / `ADMIN_PASSWORD`, created on first start). On every
start the container waits for the database and applies migrations.

| Variable | Purpose |
| --- | --- |
| `ARGUS_IMAGE` | Image to run (default `argus:latest`, built from this repository). Set a published image such as `ghcr.io/marank/argus:1` to run without the source code. |
| `APP_URLS` | All URLs users open Argus under, comma separated. Allowed hosts, CSRF origins and secure cookies (all `https`) are derived from it. |
| `TRUSTED_PROXIES` | Addresses or CIDR ranges of a TLS proxy in front; only these may pass on the client's address and scheme. |
| `APP_PORT` | Host port (default `8080`). |
| `APP_WORKERS` | Gunicorn workers (default 2 × CPU + 1, max 5). |
| `APP_DEMO_DATA` | `true` seeds an empty database with demo data. |
| `SECRET_KEY` | Django secret key (required, at least 40 random characters). |
| `TIME_ZONE`, `LOG_LEVEL` | Defaults `Europe/Berlin`, `INFO`. |
| `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` | First administrator, created on first start (later: `set_password`). Made an administrator again on every start; deactivating it in the app sticks. |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Database (also used by the Postgres container). |
| `BACKUP_TIME`, `BACKUP_KEEP_DAYS` | Daily database dump at this time (default `02:30`, in `TIME_ZONE`), kept this many days (default `14`), see [Backups](#backups). |
| `LDAP_*` | Optional LDAP / AD login, see [LDAP login](#ldap-login). |

The app container runs unprivileged with a read-only root filesystem; health
checks use `/api/health`. Behind a TLS proxy, forward `X-Forwarded-For` and
`X-Forwarded-Proto`, set `TRUSTED_PROXIES` to the proxy's address and list the
`https://` URL in `APP_URLS`. Without `TRUSTED_PROXIES` these headers are ignored, so
clients cannot fake their address (used to limit failed sign-ins) or HTTPS. A
`SECRET_KEY` turns debug off unless `DEBUG=true` is set. The API docs (`/api/docs`)
are only served with debug on. HSTS is up to the TLS proxy; Argus does not send it.

Local accounts (not LDAP) change their own password under *Sign-in & security* unless
*May change password* is off on the user; administrators set a new one under *Master
data → Employees*. Both follow Django's password validators. Without any administrator
who can sign in, set a new one in the running container (any password is accepted;
`--reset-two-factor` also switches off the second sign-in step):

```bash
docker compose exec app python manage.py set_password admin
```

## Backups

The `backup` service dumps the database every night (`BACKUP_TIME`) into the
`backups` volume and deletes dumps older than `BACKUP_KEEP_DAYS`. The dumps are in
PostgreSQL's custom format (`argus-<UTC timestamp>.dump`).

Dumps on the same host do not protect against losing the host: copy them off
regularly, or include the Docker volume in the host's backup.

```bash
docker compose exec backup sh /backup.sh now                          # dump right now
docker compose exec backup ls -l /var/lib/postgresql/backups          # list dumps
docker compose cp backup:/var/lib/postgresql/backups ./backups        # copy them off the host
```

Restore a dump (replaces the current data; stop the app so nothing writes meanwhile):

```bash
docker compose stop app
docker compose exec -T backup sh -c 'pg_restore --clean --if-exists --no-owner -d "$PGDATABASE"' < backups/argus-20261029T013000Z.dump
docker compose start app
```

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
  every user can opt out under Notifications. Mails go out through a job queue in
  PostgreSQL (Procrastinate) and are retried for about a day when the mail server
  fails; the worker in the Docker image also sends time-based reminders every hour.
  Queued, failed and finished jobs show up in the Django admin. Without PostgreSQL
  (local SQLite) mails go out directly, and `python manage.py send_reminders` sends
  reminders.
- **Live updates** – lists, dashboards, detail pages and the menu counts reload by
  themselves when someone else changes requests, problem reports, devices, licenses,
  consumables or orders. The server only signals what changed (PostgreSQL
  LISTEN/NOTIFY, sent to the browser as server-sent events); pages then load the data
  through the normal API. A page waits while one of its dialogs is open. Without
  PostgreSQL there are no signals and pages refresh as before.
- **Site settings** – modules and features can be switched off; deadlines such as
  the default and maximum loan period and warning periods are configurable.
- **Scanning** – keyboard-wedge barcode scanners work anywhere in the IT views:
  inventory number, serial, IMEI or EAN jump straight to the device or model.
  Several devices can be scanned in at once.
- **Number sequences** – configurable patterns per category
  (`{prefix}{year}-{seq}`, yearly/monthly restart) for inventory, request and
  order numbers.
- **Device names** – the inventory number belongs to the device for good; the device
  name (hostname of a PC, name of an MDE in the MDM) belongs to its place and passes
  to the replacement when a device is replaced. A category can give new devices the
  next name from a number sequence (`pc-{seq}`, `H{seq}`) or their inventory number.
  Only one device in use has a given name.
- **Self-service portal** – employees request devices by group ("any headset") or
  model, for a period or permanently, and follow status, pickup time and their
  assigned devices. Consumables that fit their own devices are offered as a quick pick.
- **Roles for IT staff** – administrators define roles (master data → Roles) that
  grant *read* or *write* per area: each master data type, requests & calendar,
  devices & service log, consumables, licenses, problem reports and procurement.
  Staff can hold several roles; rights add up. Areas without a right are hidden and
  refused by the API, though selection lists in forms keep working. Administrators
  may do everything. The areas are listed in `apps/accounts/permissions.py`.
- **Department approval** – categories can require approval (inherited by
  subcategories). Such requests wait as *awaiting approval* until an approver of the
  requester's department approves them under *Approvals* in the portal; only then
  does IT get them. Requests go straight to IT for exempt employees, when IT records
  them on someone's behalf, when the department has no approvers, and approvers'
  own requests count as approved.
- **Request workflow** – IT confirms (optionally with reduced quantities),
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

Conventions for contributors and coding agents are in [AGENTS.md](AGENTS.md).

```
backend/
  config/            settings, URLs, API assembly (config/api.py)
  apps/
    core/            base models, number sequences, auth/session API, CRUD helpers
    accounts/        users, departments, teams, LDAP and two-factor sign-in
    masterdata/      manufacturers, suppliers, categories, models, locations
    inventory/       assets, asset events, consumables and their movements
    requests/        requests, lines, allocations, workflow, employee portal
    procurement/     purchase orders, demand calculation, goods receipt
    dashboard/       overview figures
  Each app: models/, schemas/, api/, services/, admin/ – one file per concept.
  locale/            German translations

frontend/src/
  api/               typed API clients per domain
  types/             TypeScript types per domain
  components/        layout, common, crud, inventory, requests, procurement
  views/             pages per area (portal, inventory, requests, …)
  composables/       list state, actions, formatting, scanner, confirm
  i18n/locales/      en/ and de/, one file per area
  theme/             palette and Naive UI overrides (light/dark)

docs/                user and operator documentation (VitePress, German), served at /docs/
```

All models use UUIDs as primary keys (`apps.core.models.UUIDModel`, also on
`accounts.User`); URLs and API payloads carry these UUIDs. New ones are UUIDv7
(random, in creation order). `manage.py check` fails (`core.E001`) for a model of
our own without a UUID primary key.

Business rules live in `services/` (e.g. `apps/requests/services/workflow.py`);
API modules stay thin.

## Glossary

Code names on the left, the interface's German (and English) terms on the right.
URLs, API paths, permission areas and live topics say `request(s)`. "Reservierung"
is not used: a request also covers permanent hand-outs, software and consumables.
"Reserviert" stays as a device status (set aside for a request).

| Code                     | Interface (de)          | Interface (en)      |
| ------------------------ | ----------------------- | ------------------- |
| `AssetRequest`           | Anforderung             | Request             |
| `AssetRequestItem`       | Position                | Line                |
| `AssetRequestAllocation` | Zuteilung               | Allocation          |
| `Handover`               | Übergabe / Ausgabe      | Handover / hand-out |
| `DeviceReturn`           | Rückgabe                | Return              |
| `approve` (department)   | Genehmigung             | Approval            |
| `confirm` (IT)           | Bestätigung             | Confirmation        |
| `origin="direct"`        | Direktausgabe           | Direct hand-out     |
| `Asset.name`             | Gerätename              | Device name         |

The model is `AssetRequest` (variables `asset_request`), not `Request`, to avoid
confusion with the `request` argument of every API view.

## Checks

The VS Code task **Check: all** runs the same checks as CI; by hand:

```bash
cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy . && uv run deptry . && uv run pytest --cov
cd frontend && pnpm lint && pnpm format:check && pnpm type-check && pnpm test:coverage && pnpm check:licenses && pnpm build-only && pnpm size
cd docs && pnpm build
```

Coverage must not fall below the minimum: 90 % in the backend (`fail_under` in
`pyproject.toml`), a floor at today's level in the frontend (`vitest.config.ts`, about 88 % of lines; raise
it as tests are added). CI also refuses GPL/AGPL/SSPL licenses in production
dependencies (`backend/scripts/check_licenses.py`, `frontend/scripts/check-licenses.mjs`).
`pnpm lint` includes knip (unused files, exports and dependencies; `knip.jsonc`), and
the built bundle must stay within the budget in `package.json` (`size-limit`; raise it
deliberately when a feature needs it). `pnpm lint:fix` and `pnpm format` fix what they can.

CI additionally runs `manage.py check --deploy` with production settings (HSTS and the
https redirect are left to the TLS proxy and silenced in `settings.py`) and Trivy:
secrets, fixable critical vulnerabilities and Dockerfile misconfigurations fail the
build, both in the repository and in the built image; HIGH vulnerabilities are
reported.

Fast checks before every commit (ruff, prettier, oxlint, whitespace) with
[pre-commit](https://pre-commit.com), installed once:

```bash
uv tool run pre-commit install
```

The backend tests run in parallel (pytest-xdist, up to 8 workers). For a single file
or test, `-n0` skips the worker start-up, e.g.
`uv run pytest -n0 apps/accounts/tests/test_roles.py`.

## Documentation

The user and operator documentation lives in `docs/` (VitePress). Content is German,
file and folder names are English. The image serves it at `/docs/`; the user menu
links to it as *Help* (IT staff to `/docs/it/`, everyone else to `/docs/employees/`).

Three areas, each with its own navigation and search (VitePress locales):
`employees/` and `approvers/` can be linked for everyone and never link into `it/`
(the build fails otherwise); `it/` covers daily IT work, administration and operations.

```bash
cd docs
pnpm install
pnpm dev --port 5175      # http://localhost:5175/docs/; the frontend dev server proxies /docs there
pnpm build                # also fails on dead links, anchors and IT links in employees/ or approvers/
```

VS Code tasks: **Dev: docs**, **Check: docs**. Screenshots are not part of it yet.

## API types

The frontend's types for API payloads are generated from the backend's OpenAPI schema.
After changing an endpoint or a schema, run the VS Code task **API: update types**, or:

```bash
cd backend && uv run python manage.py export_openapi ../frontend/openapi.json
cd frontend && pnpm api:types
```

Commit `frontend/openapi.json` and `frontend/src/api/schema.d.ts`; CI fails when they do
not match the code. `src/types/` refers to them (`Schemas['AssetOut']`), so a changed
API shows up as a type error in the frontend.

## CI

`.github/workflows/build.yaml` runs on every push to `main`, on version tags (`v1.2.3`)
and on pull requests, also from forks. The jobs `backend`, `frontend`, `docs` and
`repository` run in parallel (the same checks as **Check: all**, plus Trivy on the
repository); `image` then builds the image, starts it against a throwaway PostgreSQL,
scans it and, except for pull requests, pushes it to `ghcr.io/marank/argus` (`latest`,
`sha-…`, and `1.2.3`/`1.2`/`1` for tags). The push uses the workflow's `GITHUB_TOKEN`;
no secrets are needed.

Repository settings on GitHub:

1. **Protect `main`** (*Settings → Branches* or *Rules*): changes only by pull request,
   with the status checks `backend`, `frontend`, `docs`, `repository` and `image` required.
2. **Renovate**: install the [Renovate GitHub app](https://github.com/apps/renovate) for
   the repository; it reads `renovate.json`. Its dependency dashboard is an issue in the
   repository; updates that need a decision (Django, Python, TypeScript majors) wait for
   approval there.
3. **Package visibility**: after the first push, make the `argus` package public
   (*Packages → argus → Package settings*), so the image can be pulled without a login.

A private mirror on Gitea or elsewhere is a pull mirror of the GitHub repository; it
runs no CI of its own.

## Translations

```bash
cd backend
uv run python manage.py makemessages -l de --ignore ".venv/*"
# edit locale/de/LC_MESSAGES/django.po
uv run python manage.py compilemessages
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and the conventions in [AGENTS.md](AGENTS.md).

## License

Argus is licensed under the [GNU Affero General Public License v3.0 or later](LICENSE).
Running a modified Argus for others over a network obliges you to offer them its source.
