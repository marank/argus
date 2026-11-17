# Sign-in and security

## Signing in

Everyone signs in on the same page with username and password, local accounts and LDAP accounts alike. Upper and lower case in the username do not matter.

By default, a sign-in is valid for 12 hours. After that, Argus reports "Your session has expired".

- **For everyone:** under **Settings → Deadlines & warnings → Session duration**, see [Settings](./settings#sign-in).
- **For individual accounts:** under **Master data → Employees** in the **Session duration (hours)** field, e.g. longer for the pickup terminal. Empty means: the value from the settings.

A changed duration applies from the next sign-in.

## Lockout after failed attempts

| Limit | Lockout |
| --- | --- |
| 10 wrong passwords for one username | 15 minutes |
| 30 wrong passwords from one address | 15 minutes |
| 10 wrong codes in the second step | 15 minutes |

A successful sign-in resets the account's counter. An administrator unlocks an account immediately by setting a new password.

## Passwords of local accounts

Local accounts are accounts without LDAP, e.g. the first administrator, terminal accounts or employees who are not in the directory. LDAP users change their password in the directory.

### Changing your own password

In the user menu under **Sign-in & security → Change password**: the current password, then the new one twice. The current session stays signed in; all other sessions of the account end.

Whether someone may change their own password is controlled by the **May change password** checkbox on the employee (on by default). Switch it off for shared accounts such as the pickup terminal.

### Password set by administrators

Under **Master data → Employees**, the **Account** section shows whether a password is set. With **Set password**, an administrator assigns a new password, e.g. for a newly created account or when someone has forgotten their password.

- The password applies immediately; existing sessions of the account end.
- Any lockout after failed attempts is lifted.
- Administrators change their own password in their profile, not here.

### Rules

New passwords have at least 8 characters, do not consist only of digits, are not a common password and are not similar to the user's name.

A newly created account has no password at first. It can only sign in once an administrator sets one or LDAP is set up.

## Two-factor sign-in

Each user can set up a second sign-in step in the user menu under **Sign-in & security**. Setting it up, switching and switching it off require the password.

| Method | How it works |
| --- | --- |
| **Authenticator app** (recommended) | Scan a QR code with an app such as Microsoft Authenticator or 1Password. At sign-in, enter the 6-digit code. |
| **Code by email** | Argus sends a code at sign-in, valid for 10 minutes. Only available with an email address and email sending set up. |

### Backup codes

During setup, Argus shows ten **Backup codes** once. Each is valid once and replaces the code when your phone or mailbox is not at hand. Store them safely: copy them or save them as a text file.

When only a few are left, Argus warns you. **Generate new codes** replaces all previous ones.

### Lost access

Without the phone and without backup codes, IT resets the two-factor sign-in: **Master data → Employees**, open the user, and under **Two-factor authentication** click **Reset**.

- Verify the identity of the person asking beforehand.
- This does not work for your own account.
- Only an administrator can reset an administrator's two-factor sign-in.

::: warning Caution
If email sending fails, users with **Code by email** can only get in with backup codes. So recommend the authenticator app.
:::

The Django admin uses the same sign-in, including the second step.

## Theme and language

In the user menu, each user chooses:

- **Language**: Deutsch or English. Emails also arrive in this language.
- **Theme**: System, Light, Solarized, Dark or Retro. **System** follows the device's setting.

Both are stored in the account and apply on all devices.
