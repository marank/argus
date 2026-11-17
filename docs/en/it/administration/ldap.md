# LDAP sign-in

Employees sign in with their directory account (LDAP or Active Directory). Argus takes the name, personnel number and other details from the directory at every sign-in.

Local accounts such as the first administrator and the pickup terminal can always sign in, with or without LDAP.

## Setting up

Under **Settings → LDAP login** (administrators only). Alternatively, set the values as [environment variables](../operations/configuration#ldap-and-active-directory); these take precedence and appear read-only in Argus.

### Server

| Field | Meaning |
| --- | --- |
| **Server URI** | e.g. `ldaps://dc1.example.com:636`. Several servers separated by commas; Argus tries them in order. |
| **StartTLS** | Upgrade `ldap://` connections to TLS |
| **Verify certificate** | On by default |
| **CA certificate file** | Path to a PEM file in the container, for an internal CA |
| **Timeout (s)** | Default 5 |

### User search

Argus looks up the user with a service account and checks the password by binding as that user.

| Field | Meaning |
| --- | --- |
| **Bind DN**, **Bind password** | Service account. Empty = anonymous search. |
| **Search base** | e.g. `OU=Staff,DC=example,DC=com` |
| **User filter** | Default: `(&(objectClass=user)(sAMAccountName={username}))` |

If you change the server, bind DN or certificate settings, enter the bind password again.

### Field mapping

| Argus field | Default attribute |
| --- | --- |
| Username | `sAMAccountName` |
| First name | `givenName` |
| Last name | `sn` |
| Personnel number | `employeeID` |
| Email | `mail` |
| Position | `title` |
| Phone | `telephoneNumber` |

Argus overwrites mapped fields at every sign-in. Username, first name and last name always come from the directory. If you leave one of the other mappings empty, that field is maintained in Argus.

### Test connection

**Test connection** checks the entered values that have not been saved yet. With a username, Argus also shows which values this user would receive. The user's password is not checked.

### Creating users

With **Create users on first login** (the default), the Argus account is created at the first sign-in. If it is off, only users who already exist in Argus can sign in via LDAP.

## What happens at sign-in

1. Argus checks local accounts first, then the directory.
2. The filter must find exactly one entry.
3. Argus looks for the matching Argus account: first by the directory entry, then by the username (case-insensitive).
4. If there is none, Argus creates it. The username is lowercased.
5. Mapped fields are updated.
6. Teams with an **LDAP group** sync their members. Nested groups do not count.

::: info Good to know
- A local administrator is never taken over by a directory account.
- An existing local account with the same username is linked to the directory. If it has a local password, that password remains valid.
- The account must be active in Argus.
- If the directory is unreachable, the sign-in fails as it does with a wrong password.
:::

## Syncing users

**Sync LDAP users** creates or updates employees in advance, without them having to sign in. This lets you, for example, record requests for new colleagues before they sign in for the first time.

1. Switch on the LDAP login and save; the sync uses the saved configuration.
2. Enter an **LDAP filter** or choose a template: **Same as login filter**, **Active AD accounts only** or **Member of a group**.
3. **Preview** shows for each entry whether it will be created, updated, left unchanged or skipped, with all changes.
4. Select entries and click **Apply**.

The preview changes nothing. Up to 5000 entries are possible.

::: warning Caution
- The sync only runs when you start it. There is no schedule.
- Argus does not deactivate accounts. Anyone locked or deleted in the directory stays active in Argus but can no longer sign in. Deactivate such accounts in Argus yourself.
- The sync creates accounts even when **Create users on first login** is off.
:::
