# Updates and troubleshooting

## Updating to a new version

1. Back up first:

   ```bash
   docker compose exec app python manage.py backup_database
   ```

2. Start the new version, depending on the [installation method](./installation):

   **Using the prebuilt image:** `pull` fetches the current state.

   ```bash
   docker compose pull app
   ```

   ```bash
   docker compose up -d
   ```

   **From the repository:**

   ```bash
   git pull
   ```

   ```bash
   docker build -t argus:latest .
   ```

   ```bash
   docker compose up -d
   ```


On start, Argus applies the database migrations automatically. During the restart, Argus is unreachable for a few seconds.

## Checking the state

| Check | Command |
| --- | --- |
| Are all services running? | `docker compose ps` |
| Is Argus reachable? | `curl -fsS http://localhost:8080/api/health` |
| View the log | `docker compose logs -f app` |

`/api/health` is reachable without signing in and also serves as Docker's health check. The status `healthy` in `docker compose ps` means that the web interface and the API respond.

Several processes run in the `app` container: nginx, the application, a process for live updates and a worker for background jobs (emails, reminders). If one of them fails repeatedly, the container exits. Docker then restarts it, and the cause is in the log.

## Resetting a password

Normally an administrator sets the password directly in Argus, see [Passwords of local accounts](../administration/sign-in#passwords-of-local-accounts).

On the command line, this also works without signing in, e.g. when no administrator can sign in any more:

```bash
docker compose exec app python manage.py set_password admin
```

The command asks for the new password twice and lifts a lockout after failed attempts for this account. With `--reset-two-factor`, it also disables the user's two-factor authentication.

Unlike Argus, the command does not check the password rules. LDAP users change their password in the directory.

::: warning Caution
Do not set a local password for an LDAP user. Argus checks the local password first; it would be valid alongside the directory password.
:::

## Maintenance commands

All commands run in the `app` container: `docker compose exec app python manage.py <command>`.

| Command | Purpose |
| --- | --- |
| `set_password <user>` | Set a new password, lift the lockout. Options: `--password`, `--reset-two-factor` |
| `send_reminders` | Send due return and license reminders immediately. The worker does this every hour anyway. |
| `seed_demo` | Create demo data, for test instances only |
| `createsuperuser` | Create another local administrator |

## Background jobs

Emails and reminders run through a queue in the database. If the mail server cannot accept a message, Argus retries for about a day. The Django admin at `/admin/` shows waiting, failed and completed jobs (administrators only).

The worker sends reminders (returns, license expiries) every hour. It deletes completed jobs after 24 hours and failed ones after 14 days. Read notifications in the app disappear after 90 days.

If sending emails is disabled, Argus no longer sends emails that are already waiting either.

## Common problems

### Sign-in fails immediately or the page reports a CSRF error

The address you opened is missing from `APP_URLS`, or Argus runs behind a TLS proxy whose address is not in `TRUSTED_PROXIES`. See [Behind a TLS proxy](./installation#behind-a-tls-proxy).

### The container does not start

The most common causes in the log (`docker compose logs app`):

- `SECRET_KEY` is missing, shorter than 40 characters or a placeholder such as `change-me`.
- The database is unreachable: `POSTGRES_PASSWORD` does not match the password the database volume was created with.

### Changes by others only appear after reloading

The proxy buffers the live updates. Disable buffering for `/api/events`, see [Live updates through the proxy](./installation#live-updates-through-the-proxy).

### Argus stops loading once several tabs are open

Argus is opened directly over HTTP, without an HTTP/2-capable proxy. Browsers then allow only six connections per address. Solution: put a TLS proxy with HTTP/2 in front.

### Emails do not arrive

1. Under **Settings → Email**, check whether **Send emails** is enabled, and send a test email. The test email goes out even when sending is disabled. If it arrives but normal emails do not, this switch is usually the reason.
2. In the Django admin, check the failed jobs and their error messages.
3. Check whether the notification type is enabled under **Settings → Notifications** and the recipient has not unsubscribed from it.
4. Check whether the recipient has an email address.

### A newly created user cannot sign in

Users created in Argus have no password at first. They sign in via LDAP, or an administrator sets one under **Master data → Employees** with **Set password**.

### The pickup terminal is signed out

The sign-in has expired, by default after 12 hours. Enter a longer **Session duration (hours)** on the terminal account, see [Sign-in and security](../administration/sign-in#signing-in).
