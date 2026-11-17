# Installation

Argus runs as a Docker Compose project with two services:

| Service | Purpose |
| --- | --- |
| `app` | Argus itself: web interface, API, background jobs, live updates and the nightly backup (see [Backups](./backups)) in one container |
| `db` | PostgreSQL database |

## Prerequisites

- A Linux server with Docker Engine and the Compose plugin
- For production, a TLS proxy in front (e.g. nginx, Traefik or Caddy), see [Behind a TLS proxy](#behind-a-tls-proxy)
- Optionally an SMTP server for emails and an LDAP or Active Directory server for sign-in

There are two ways:

| Way | When |
| --- | --- |
| [Using the prebuilt image](#using-the-prebuilt-image) | Recommended. The server only needs two files and access to `ghcr.io`. |
| [Building from the repository](#building-from-the-repository) | For your own changes to the code. The image is built on the server. |

## Using the prebuilt image

The CI publishes Argus publicly as `ghcr.io/marank/argus:latest`, the current state of `main`. This image is preset in `compose.yml`.

1. Create a directory, e.g. `/opt/argus`, and put `compose.yml` and `.env.example` from the repository into it.

2. Create the configuration, see [Creating the configuration](#creating-the-configuration).

3. Pull the image and start Argus with its database:

   ```bash
   docker compose pull app
   ```

   ```bash
   docker compose up -d
   ```

## Building from the repository

1. Get the repository onto the server:

   ```bash
   git clone https://github.com/marank/argus.git /opt/argus
   ```

2. Create the configuration, see [Creating the configuration](#creating-the-configuration), and enter the image you build yourself:

   ```ini
   ARGUS_IMAGE=argus:latest
   ```

3. Build the image and start:

   ```bash
   docker build -t argus:latest .
   ```

   ```bash
   docker compose up -d
   ```

## Creating the configuration

The same for both ways:

```bash
cp .env.example .env
```

In `.env`, set at least these values:

| Variable | Value |
| --- | --- |
| `APP_URLS` | The address at which Argus is reachable, e.g. `https://argus.example.com` |
| `SECRET_KEY` | Random value with at least 40 characters |
| `ADMIN_PASSWORD` | Password of the first administrator |
| `POSTGRES_PASSWORD` | Password of the database |

This generates a suitable random value for `SECRET_KEY` and `POSTGRES_PASSWORD`:

```bash
openssl rand -hex 32
```

All other variables are listed under [Configuration](./configuration).

## After starting

Argus is reachable at `http://<server>:8080` (change the port with `APP_PORT`). Sign in with `ADMIN_USERNAME` (default `admin`) and `ADMIN_PASSWORD`.

On every start, the container waits for the database, applies pending migrations and makes sure the first administrator exists.

::: info Good to know
- `ADMIN_PASSWORD` is only used when the user is created. Later changes in `.env` have no effect. Change the password after your first sign-in under **Sign-in & security**.
- The first administrator gets administrator rights again on every start. If you revoke the rights in Argus, this only lasts until the next restart. Deactivating the account, on the other hand, persists.
- Argus does not start without a valid `SECRET_KEY`: it is missing, shorter than 40 characters or a placeholder such as `change-me`.
:::

## Test instance with demo data

With `APP_DEMO_DATA=true`, Argus fills a database without devices with sample data on start: about 150 devices with history, requests at every stage, purchase orders, licenses and problem reports. All demo users have the password `argus-demo`:

| User | Role |
| --- | --- |
| `admin` | Administrator |
| `it` | IT department |
| `employee`, `sales` | Employees |
| `terminal` | Pickup terminal |

If devices have already been recorded, Argus does not create demo data.

::: danger Important
Never enable demo data on a production instance: the demo users have a known password.
:::

## Behind a TLS proxy

The container only speaks HTTP on port 8080. For production, put a TLS proxy in front of it.

1. The proxy forwards to `http://<server>:8080` and sets the headers `X-Forwarded-For` and `X-Forwarded-Proto`.
2. `APP_URLS` contains the `https://` address.
3. `TRUSTED_PROXIES` contains the IP address (or CIDR range) of the proxy.

```ini
APP_URLS=https://argus.example.com
TRUSTED_PROXIES=10.0.0.5
```

Only requests from the addresses in `TRUSTED_PROXIES` may pass on the client address and HTTPS. Without this entry, Argus ignores these headers. Sign-ins over HTTPS then fail. In addition, all users share the proxy's address, so the lockout after failed attempts (30 per address in 15 minutes) hits all of them at once. The container warns on start when `APP_URLS` contains HTTPS addresses but `TRUSTED_PROXIES` is empty.

### Live updates through the proxy

For each open tab, Argus keeps a connection to `/api/events` open, through which changes arrive immediately. The proxy must not buffer this connection:

- **nginx:** set `proxy_buffering off;` for `/api/events`
- **Traefik, Caddy:** usually pass the stream through without changes

If the proxy speaks HTTP/2 with the browser, there is no limit on the number of tabs. If Argus is opened directly via `http://…:8080`, browsers allow only six simultaneous connections per address. From about six open Argus tabs on, further requests then hang until a tab is closed.

Argus does not set HSTS itself; that is the proxy's job.

## Next steps

- [Configuration](./configuration): all environment variables
- [Getting started for administrators](../administration/getting-started): from an empty instance to production
- [Backups](./backups): check the backup and copy it off-site
