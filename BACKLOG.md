# Backlog

Open points that are known but not yet decided or done.

## Live updates (`/api/events`)

### Find out how Argus is reached in production

Everything below depends on it: through a TLS proxy (which one?) or directly on
port 8080 of the container?

### Six-connection limit over HTTP/1.1

Each open Argus tab holds one server-sent events connection. Over HTTP/1.1 browsers
allow only six connections per origin, so from about six open tabs on, normal API
requests hang until a tab is closed.

The container's nginx speaks HTTP/1.1 only: browsers use HTTP/2 over TLS only, and
the container listens without TLS on 8080 (TLS is the job of a proxy in front).

- Behind a TLS proxy that speaks HTTP/2 to browsers: no problem, HTTP/2 multiplexes
  all requests over one connection.
- Reached directly via `http://…:8080`: the limit applies.

Options if it applies: put an HTTP/2 TLS proxy in front, or share one stream per
browser instead of one per tab (`SharedWorker`, or a leader tab that forwards the
signals over `BroadcastChannel`).

### Outer proxy must not buffer the stream

The container's nginx sets `X-Accel-Buffering: no` for `/api/events` but consumes
the header itself, so it does not reach a proxy in front. An outer nginx then
buffers the events and delivers them late and in batches. Either switch buffering
off there for `/api/events` (`proxy_buffering off`), or have the container's nginx
pass the header on (`add_header X-Accel-Buffering no always;` in that location; it
must then include the security headers again, since `add_header` in a location
replaces the inherited ones). Traefik and Caddy usually pass the stream through
unbuffered.

### Live updates in local development

Locally there are none: SQLite has no LISTEN/NOTIFY, and `runserver` is WSGI, where
`/api/events` answers 204 even with PostgreSQL. To have them: run PostgreSQL
(e.g. the `db` service of compose.yml), uvicorn for `/api/events` next to
runserver, and route that path to uvicorn in the Vite proxy; add a launch
configuration for it.

Note for development against PostgreSQL (`DB_HOST` set): the job queue is on, so
mails and reminders stay queued unless
`uv run python manage.py procrastinate worker` runs as well.

### Pages without live updates

- Purchase order detail page: its edit form would be overwritten. Could reload while
  the form is unchanged, or offer a "changed by someone else, reload?" hint.
- Pickup terminal: still polls every 30 seconds; it could listen to `request`.

## Operations

### Backups in the frontend

The job worker dumps the database nightly (`apps/core/services/backups.py`), configured
by `BACKUP_TIME` and `BACKUP_KEEP_DAYS`. Idea: time and retention under Settings, a list
of the dumps with their size, a "Back up now" button, and a warning on the dashboard
when the last dump failed or is older than a day.

### Updating an installation that runs a published image

With `ARGUS_IMAGE`, `docker compose pull app` updates the app, but changes to
`compose.yml` or `.env.example` in a new version have to be copied by hand. Decide how
to ship them (release notes, a versioned compose file, or a check at start that warns
about missing variables).

## Wording: "Gerät" (device)

The German UI says "Gerät"/"Geräte" for about 200 strings (requests 42, inventory 42,
backend messages 67, also terminal, handover, dashboard, nav), but means three things:

| Meaning | Examples | Proposal |
| --- | --- | --- |
| A serialized item with an inventory number (`Asset`) | notebook, MDE, MDE handle, docking station | "Asset" ("Assets", "Asset ersetzen"); matches "IT-Asset-Verwaltung" and the code |
| Everything someone requests or receives | request lines, hand-out, terminal, "Meine Geräte" | "Ausstattung" ("Meine Ausstattung", "Bitte prüfen Sie Ihre Ausstattung"); covers cables, accessories, toner |
| One concrete item whose kind is known | a handle in a request | the category's singular name ("Handgriff", "Notebook"), which exists already |

"Gerät" would stay only where it really means a device, e.g. the device name
(hostname). Touches German and English UI texts, backend messages (`django.po`), the
docs and the glossary in README. Decide the terms first, then change everything in one
go.
