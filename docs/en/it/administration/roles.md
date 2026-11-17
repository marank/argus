# Roles and permissions

Argus distinguishes four kinds of users. For IT staff, roles control which areas they see and can change.

## Kinds of users

| Kind | Flag | Sees |
| --- | --- | --- |
| **Employee** | – | Dashboard, self-service and their own profile |
| **IT staff** | **IT staff** | Additionally the IT areas, depending on their roles |
| **Administrator** | **Administrator** | Everything, including roles and settings |
| **Pickup terminal** | **Pickup terminal** | Only the [pickup terminal](../terminal) |

**Approver** is not a separate kind: anyone entered as an approver on a department additionally sees **Approvals**.

You set the flags under **Master data → Employees**. Only administrators can make someone an administrator.

## Roles

An administrator creates roles under **Master data → Roles**. Each role has members and a level for each area:

| Level | Effect |
| --- | --- |
| **No access** | The area is hidden. |
| **Read** | The area is visible, without the option to change anything. |
| **Write** | View and change |

### Areas

**Master data:** Models, Categories (including components), Manufacturers, Suppliers, Locations, Departments, Teams, Employees, Number sequences

**IT operations:** Requests & calendar, Devices & service log, Consumables, Licenses, Problem reports, Procurement

### How permissions combine

- A user can have several roles. For each area, the highest level across all roles applies.
- Roles only take effect for **IT staff**. An employee without this flag has no IT permissions, even with a role.
- Administrators always have all permissions, regardless of roles.
- A new IT staff member without a role does not see any IT areas yet.
- Selection lists in forms work even without permission for the area. Someone who handles requests can, for example, select locations without seeing location management.

::: tip Tip
A few clearly defined roles work best, e.g. "Service Desk" (write requests, devices, problem reports; read master data) and "Purchasing" (write procurement, suppliers).
:::

## What only administrators can do

- Create and assign roles
- Make users administrators, change and delete administrators, and reset their two-factor sign-in
- Everything under **Administration → Settings**

An administrator can neither deactivate themselves nor remove their own administrator rights.

::: info Good to know
- Anyone with write access to **Employees** can turn others into IT staff or terminal accounts. They only get permissions through a role, which only an administrator assigns.
- Notifications to "IT" go to all IT staff, regardless of their roles, unless a team is responsible. An administrator without the **IT staff** flag does not receive them.
- The first administrator from the installation gets administrator rights back on every restart.
:::
