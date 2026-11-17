# Email and notifications

Argus notifies in two ways: by **email** and **in the app** via the bell at the top right. Administrators decide what is available at all; each user can switch off individual notifications for themselves.

## Setting up email sending

Under **Settings → Email**:

| Field | Meaning |
| --- | --- |
| **Send emails** | Main switch, off by default |
| **Server** | SMTP server |
| **Port & encryption** | **STARTTLS** (usually port 587), **SSL/TLS** (usually port 465) or **None**. You adjust the port yourself. |
| **User name**, **Password** | Sign-in to the server. An empty password field keeps the stored password. |
| **Sender address**, **Sender name** | How the emails appear to the recipient |
| **App address** | Address of Argus, e.g. `https://argus.example.com`. Without it, emails contain no links. |

Save first, then send a test email with **Send test email**. The test email is sent even when the main switch is off; Argus shows server errors directly.

::: info Good to know
- Emails are sent in the recipient's language.
- If the mail server is temporarily unreachable, Argus keeps retrying for about a day.
- If you switch off **Send emails**, Argus also stops sending emails that are already waiting.
- The SMTP password is stored in the database and therefore also in the backups.
:::

## Setting notifications for everyone

Under **Settings → Notifications**, you switch each notification on or off per channel (email, in the app), separately by recipient. By default everything is switched on.

### To employees

| Notification | When |
| --- | --- |
| **Request confirmed** | IT has confirmed, with a comment |
| **Request declined** | IT or the approver has declined, with a reason |
| **Cancelled by IT** | IT has cancelled the request |
| **Ready for pickup** | With time and place; IT can leave it out in individual cases |
| **Handover changed** | Time, place or type changed after the ready-for-pickup notice |
| **Handed out** | What was handed out and when it must be returned |
| **Loan extended** | With the new return date |
| **Taken back** | What was taken back and what is still outstanding |
| **Return reminder** | A few days before the return |
| **Return overdue** | Once, as soon as the return is overdue |
| **Message on problem report** | IT has written on a problem report |
| **Problem report resolved** | With IT's message |

### To IT

| Notification | When |
| --- | --- |
| **New request** | A request has reached IT |
| **New problem report** | An employee has reported a problem |
| **Reply on problem report** | The reporter has written or marked the problem report as resolved |
| **Assigned to me** | Someone has assigned a request or problem report to you |
| **License ending** | A time-limited license ends within the warning period |

New requests and problem reports go to the responsible team, otherwise to all IT staff.

### To approvers

| Notification | When |
| --- | --- |
| **Approval needed** | A request from the department is waiting for approval. Also goes to an active delegate. |

### Reminder by IT

**Send return reminder** on a request immediately sends the employee an email. It is sent regardless of all switches.

## Setting notifications for yourself

Each user chooses in the user menu under **Notifications** which notifications they receive by email and in the app. Only what an administrator has switched on can be switched off.

- Without your own email address, or without email sending set up, the email switches are locked. Your own address is maintained by IT or LDAP.
- Only IT sees IT notifications, and only approvers see approver notifications.

Inactive users and terminal accounts never receive notifications. Argus deletes read in-app notifications after 90 days.
