# Dashboard and calendar

## Dashboard

The IT dashboard shows the current state of inventory, requests and procurement. Everyone sees only widgets for areas they have permissions for and whose module is switched on.

### Default widgets

| Widget | Content |
| --- | --- |
| **My work** | Open requests by responsibility: assigned to me, my teams, unassigned; plus my problem reports |
| **Requests** | To confirm, to prepare, ready for handover, overdue returns |
| **Procurement & stock** | To order, ordered and on the way, below minimum stock |
| **Deadlines & reports** | Open problem reports, expiring licenses and warranties |
| **Devices by status** | Distribution of all devices |
| **Upcoming hand-outs** | What is to be handed out in the next few days, with overdue items highlighted |
| **Recent activity** | The last ten steps from all areas you may read; handing out several devices is one line. **Show all** opens [Activities](./activities) |

Clicking any number takes you to the matching, filtered list.

### More widgets

With **Customize dashboard → Add widget**:

- **My tasks**: requests and problem reports assigned to you personally
- **Overdue returns**: with a **Remind** button
- **This week**: calendar entries for the next 7 days
- **Team workload**: open requests and problem reports per person
- **Requests per week**: new and completed requests over the last 12 weeks
- **Returns due soon**, **Waiting requests**, **Expiring licenses & warranties**, **Consumables running low**, **Open orders**
- **Shortcuts**: buttons to pages of your choice
- **Notes**: a personal notepad, visible only to you

### Customizing

**Customize dashboard** opens edit mode:

- move widgets by drag and drop
- choose **Width** (Third, Half, Full) and **Height**
- hide individual figures with the eye icon
- set a **Custom title**

Some widgets can be added several times, each with its own settings. **Restore default** resets the dashboard. The layout is saved per user.

Administrators set the warning periods for licenses and warranties in the [Settings](./administration/settings#deadlines-warnings).

## Calendar

**IT operations → Calendar** shows all IT dates. Views: **Month**, **Week** and **List**.

| Entry | Content |
| --- | --- |
| **Request** | Temporary loans as bars from start to end date |
| **Pickup** | Agreed pickup date, otherwise the preferred date or start date |
| **Return due** | Returns due. Overdue ones move along day by day until they are done. |
| **Delivery** | Expected delivery dates of open purchase orders |
| **Warranty ends** | One combined entry per day for all devices whose warranty ends |
| **License ends** | End date of time-limited licenses |

- **Solid** = confirmed, **outline only** = not yet confirmed, **red** = overdue.
- Permanent hand-outs do not appear as bars, but their pickup day does.
- With the tabs at the top, you limit requests to **Assigned to me**, **My teams** or **Unassigned**.
- With the filters, you hide entry types. Argus remembers the selection in the browser.

Warranty, license and delivery dates can be switched off individually in the [Settings](./administration/settings).

::: info Good to know
The calendar does not refresh by itself. Reload it to see changes made by others.
:::
