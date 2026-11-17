# Architecture

The rules behind this layout (one file per model, services, strict typing, i18n) are in
[AGENTS.md](https://github.com/marank/argus/blob/main/AGENTS.md).

## Layout

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
  types/             TypeScript types per domain (aliases of the generated schema)
  components/        layout, common, crud, inventory, requests, procurement
  views/             pages per area (portal, inventory, requests, …)
  composables/       list state, actions, formatting, scanner, confirm
  i18n/locales/      en/ and de/, one file per area
  theme/             palette and Naive UI overrides (light/dark)

docs/                this documentation (VitePress), served at /docs/
docker/              nginx, supervisord, gunicorn and the entrypoint of the image
```

## Conventions

- **UUID keys.** All models use UUIDs as primary keys (`apps.core.models.UUIDModel`,
  also on `accounts.User`); URLs and API payloads carry these UUIDs. New ones are UUIDv7
  (random, in creation order). `manage.py check` fails (`core.E001`) for a model of our
  own without a UUID primary key.
- **Services.** Business rules live in `services/` (e.g.
  `apps/requests/services/workflow.py`); API modules stay thin.
- **Code and data in English**, German ships as translation (backend `locale/`,
  frontend `src/i18n/locales/de`).

## Runtime

One image runs nginx (serves the built frontend and these docs, proxies `/api` and
`/admin`), gunicorn (Django), uvicorn for the live update stream (`/api/events`) and the
Procrastinate job worker, all under supervisord. docker compose adds PostgreSQL.

- **Jobs:** mails, reminders and the nightly backup go through a Procrastinate queue in
  PostgreSQL. With SQLite there is no queue; jobs run in-process right after the
  transaction commits.
- **Live updates:** the server signals what changed (PostgreSQL LISTEN/NOTIFY, sent to the
  browser as server-sent events); pages then reload their data through the normal API.

## Domain terms

Code names on the left, the interface's terms on the right. URLs, API paths, permission
areas and live topics say `request(s)`. "Reservierung" is not used: a request also covers
permanent hand-outs, software and consumables. "Reserviert" stays as a device status (set
aside for a request).

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
