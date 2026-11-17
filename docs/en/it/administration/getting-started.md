# Launch checklist

From a freshly installed instance to live operation. The installation itself is described in [Installation](../operations/installation).

## Checklist

### 1. Basic settings

- Sign in with the first administrator and set up [two-factor sign-in](./sign-in#two-factor-sign-in).
- Under **Settings → Modules & features**, switch off what you do not need.
- Under **Settings → Deadlines & warnings**, set the loan period and reminders.

### 2. Email

- Under **Settings → Email**, enter the SMTP server, set the **App address** and switch on **Send emails**.
- Send a test email.
- Under **Settings → Notifications**, check which notifications should exist.

See [Email and notifications](./email).

### 3. Sign-in

- Set up LDAP and check it with **Test connection**, see [LDAP sign-in](./ldap).
- Create employees in advance with **Sync LDAP users**.

### 4. Master data

- Create number sequences for inventory numbers and, if needed, device names.
- Create locations with storage locations and pickup points.
- Create departments with approvers.
- Create IT teams and set a default team.
- Create manufacturers and suppliers.
- Create categories with number sequence, team, portal settings and approval requirement.
- Create models.

See [Master data](./master-data).

### 5. IT team

- Create roles, see [Roles and permissions](./roles).
- Mark IT staff as **IT staff** and give them roles and teams.

### 6. Inventory

- Import devices, see [Importing devices](../device-import).
- Create consumables with minimum stock levels and book them in.
- Record licenses and assign them.

### 7. Pickup terminal

- Create a terminal account, set a password and sign in on the touch PC. See [Pickup at the terminal](../terminal#setup).

### 8. Operations

- Check the TLS proxy and `TRUSTED_PROXIES`.
- Copy backups off-site and test a restore, see [Backups](../operations/backups).

## Afterwards

- Point employees to [Getting started for employees](../../employees/getting-started).
- Point IT to [Getting started for IT](../getting-started).
