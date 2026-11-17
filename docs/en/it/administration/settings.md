# Settings

Under **Administration → Settings**, administrators configure Argus for all users. The page has five sections:

1. Modules & features
2. Deadlines & warnings
3. [Email](./email#setting-up-email-sending)
4. [Notifications](./email#setting-notifications-for-everyone)
5. [LDAP login](./ldap)

## Modules & features

Switches take effect immediately, without saving. By default everything is switched on.

### Modules

| Module | What disappears when it is off |
| --- | --- |
| **Consumables** | Consumables management and quick pick in self-service |
| **Software & licenses** | Licenses, **My software**, license warnings |
| **Procurement** | Demand and purchase orders |
| **Calendar** | The IT calendar |
| **Problem reports** | Problem reports in IT and self-service, **Report a problem** |
| **Pickup terminal** | The pickup terminal |

Switched-off areas disappear from menus and pages. The data is kept; once you switch the module back on, everything is there again.

### Features

| Feature | Effect | Requires |
| --- | --- | --- |
| **Warranty ends in the calendar** | One combined entry per day | Calendar |
| **License expiry in the calendar** | End dates of time-limited licenses | Calendar, Licenses |
| **Deliveries in the calendar** | Expected delivery dates | Calendar, Procurement |
| **Consumables quick pick** | Matching supplies for your own devices when requesting | Consumables |
| **Request software** | Software categories in self-service | Licenses |
| **Attention animations** | Pulsing markers on elements waiting to be handled | – |

A feature only works while all the modules it requires are switched on. Otherwise it is grayed out.

## Deadlines & warnings

### Loans

Applies to time-limited requests.

| Setting | Default | Effect |
| --- | --- | --- |
| **Default loan period** | 5 days | Suggested period when requesting, including the start day |
| **Maximum loan period** | 0 = unlimited | Argus rejects longer periods when requesting, for direct hand-outs and quick assignments. Extensions by IT are not limited. |
| **Return reminder** | 2 days | Argus reminds the employee this many days before the return date. 0 = on the return day. |

### Warning periods

When warranties and licenses count as "expiring soon".

| Setting | Default | Effect |
| --- | --- | --- |
| **Warranty** | 60 days | Dashboard and widgets |
| **Licenses** | 60 days | Dashboard, list and the **License ending** notification |

### Sign-in

| Setting | Default | Effect |
| --- | --- | --- |
| **Session duration** | 12 hours | How long a sign-in stays valid (1 to 720 hours). Applies from the next sign-in; a value set on the employee takes precedence. |
