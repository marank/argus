# Configuration

Argus is configured through environment variables in the file `.env` in the project directory. After a change, `docker compose up -d` applies the new values.

Settings that change during operation (modules, deadlines, email server) are not configured here but under [Settings](../administration/settings) in Argus.

## Application

| Variable | Default | Meaning |
| --- | --- | --- |
| `ARGUS_IMAGE` | `ghcr.io/marank/argus:latest` | The image that runs. For an image you build yourself `argus:latest`, see [Installation](./installation#building-from-the-repository). |
| `APP_URLS` | `http://localhost:8080` | All addresses at which Argus is opened, comma-separated. From these, Argus derives allowed hosts, CSRF origins and secure cookies. |
| `APP_PORT` | `8080` | Port on the host |
| `APP_WORKERS` | 2 × CPU + 1, at most 5 | Number of Gunicorn processes |
| `APP_DEMO_DATA` | `false` | `true` fills a database without devices with demo data |
| `TRUSTED_PROXIES` | empty | IP addresses or CIDR ranges of the TLS proxy, comma-separated |
| `SECRET_KEY` | – | Required. Random value with at least 40 characters, no placeholder such as `change-me` |
| `TIME_ZONE` | `Europe/Berlin` | Time zone for appointments, reminders and backups |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING` or `ERROR` |
| `DEBUG` | `false` (with `SECRET_KEY`) | For development only. Among other things, enables the API documentation at `/api/docs`. |

::: warning Caution
Every address at which Argus is opened must be listed in `APP_URLS`, with scheme, host and port if needed. If one is missing, Argus rejects requests via that address.
:::

## First administrator

| Variable | Default | Meaning |
| --- | --- | --- |
| `ADMIN_USERNAME` | `admin` | User name |
| `ADMIN_EMAIL` | – | Email address |
| `ADMIN_PASSWORD` | – | Password, only used when the account is first created |

## Database

| Variable | Default | Meaning |
| --- | --- | --- |
| `POSTGRES_DB` | `argus` | Name of the database |
| `POSTGRES_USER` | `argus` | Database user |
| `POSTGRES_PASSWORD` | – | Required. Password of the database user |

## Backups

| Variable | Default | Meaning |
| --- | --- | --- |
| `BACKUP_TIME` | `01:30` | Time of the daily backup (in `TIME_ZONE`) |
| `BACKUP_KEEP_DAYS` | `14` | Retention period in days |
| `BACKUP_DIR` | `/backups` | Target in the container (volume `db-backups`). Empty disables the nightly backup. |

See [Backups](./backups).

## LDAP and Active Directory

You can set up LDAP sign-in entirely in Argus (see [LDAP sign-in](../administration/ldap)). Each variable you set overrides the value from Argus; it then appears there as read-only.

| Variable | Meaning |
| --- | --- |
| `LDAP_ENABLED` | `true` enables LDAP sign-in |
| `LDAP_SERVER_URI` | Servers, comma-separated, e.g. `ldaps://dc1.example.com,ldaps://dc2.example.com` |
| `LDAP_START_TLS` | StartTLS on an `ldap://` connection |
| `LDAP_VERIFY_CERT` | Verify the server's certificate |
| `LDAP_CA_CERT_FILE` | Path to a CA file (PEM) in the container, for an internal CA |
| `LDAP_TIMEOUT` | Timeout in seconds |
| `LDAP_BIND_DN`, `LDAP_BIND_PASSWORD` | Service account for the user search; empty = anonymous search |
| `LDAP_USER_SEARCH_BASE` | Search base, e.g. `OU=Staff,DC=example,DC=com` |
| `LDAP_USER_FILTER` | Search filter with the placeholder `{username}` |
| `LDAP_CREATE_USERS` | Create users on their first sign-in |
| `LDAP_ATTR_USERNAME` | Attribute for the user name (default `sAMAccountName`) |
| `LDAP_ATTR_FIRST_NAME` | First name (default `givenName`) |
| `LDAP_ATTR_LAST_NAME` | Last name (default `sn`) |
| `LDAP_ATTR_EMPLOYEE_NUMBER` | Employee number (default `employeeID`) |
| `LDAP_ATTR_EMAIL` | Email (default `mail`) |
| `LDAP_ATTR_JOB_TITLE` | Job title (default `title`) |
| `LDAP_ATTR_PHONE` | Phone (default `telephoneNumber`) |

For an internal CA, mount the PEM file as a volume into the `app` container and set `LDAP_CA_CERT_FILE` to its path.
