# Security

An overview of how Argus is secured and what operations contribute to it.

## Container

- The `app` container runs as an unprivileged user, without Linux capabilities and with a read-only file system. Only `/tmp` in memory is writable.
- `no-new-privileges` prevents privilege escalation through setuid programs.
- Code and configuration in the image belong to `root`; the application can read them but not change them.
- The nightly backup runs inside the `app` container. Only its user can read the backup files, because they contain password hashes and personal data.

## In the browser

- Sign-in via session cookies with CSRF protection. A sign-in lasts 12 hours by default; adjustable for everyone and per account. The cookies are marked `Secure` when all addresses in `APP_URLS` use HTTPS.
- A Content Security Policy allows scripts, fonts and connections only from Argus itself. Argus loads nothing from third-party servers.
- Argus may only be embedded by itself (protection against clickjacking).

## Sign-in

- Passwords are stored with Argon2.
- After failed attempts, Argus blocks further sign-ins for 15 minutes: after 10 wrong passwords for a user name, after 30 from one address, and after 10 wrong codes in the second step. For the lockout to apply per client rather than per proxy, `TRUSTED_PROXIES` must be set.
- Every user can set up [two-factor authentication](../administration/sign-in).
- The Django admin at `/admin/` uses the same sign-in, including the second factor.

## What operations must contribute

- Serve Argus only over HTTPS; set HSTS at the proxy.
- Keep `SECRET_KEY` and `.env` secret. Anyone who knows the `SECRET_KEY` can forge sessions.
- Keep backups outside the server and protect them against unauthorized access. They also contain the passwords for SMTP and the LDAP service account, if these are stored in Argus rather than set via environment variables.
- Install new versions promptly. The image is scanned for known vulnerabilities when it is built.
