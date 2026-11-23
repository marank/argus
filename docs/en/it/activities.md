# Activities

**IT operations → Activities** shows who did what and when: in requests, devices, consumables, licenses, problem reports and orders. The newest entries are at the top. The **Recent activity** widget on the [dashboard](./dashboard-calendar) shows the last ten; **Show all** opens the page.

Each row is one step of work. If it covers several devices or items, it still appears only once, with the count:

- Handing out a request with three devices is one row **Handed out · 3 items**, linking to the request.
- A goods receipt is one row **Delivery received**, even if devices are created and stock is booked in.
- Creating a series or an [import](./device-import) is one row **Devices created** or **Devices imported**.

The exception are allocations while preparing a request: every device, consumable or license allocated or removed again is a row of its own, **Allocated** or **Allocation removed**, with the device, e.g. **Allocated · NB-0012 · ThinkPad T14**. If **Allocate automatically** or a goods receipt allocated it, this is noted in brackets.

## Columns

| Column | Content |
| --- | --- |
| **Time** | When the step was recorded |
| **Area** | Requests, devices, consumables, licenses, problem reports or orders |
| **Object** | The request, device, license etc.; a click opens it |
| **Activity** | What was done, with the count where it applies |
| **Performed by** | Who did it |
| **Employee** | Whom it concerns, e.g. the requester |
| **Detail** | Comment or description; can be shown via **Columns** |

You can filter by **Area**, **Activity**, **Performed by** and **Time**; the search finds objects, details and names.

## Detailed history of a request {#detailed-history}

**Detailed history** in the **History** card of a [request](./requests#history) opens this page with only the entries of that request. It lists every step, including each single allocation and removal with person and time. **Show all** lifts the restriction.

::: info Good to know
- You only see entries from areas you may read.
- Deleted devices, licenses and orders stay in the list with their name, but without a link.
- Changes to master data, users, roles and settings do not appear here.
- Single allocations are recorded from this version on. For older requests only the finished preparation is listed.
- Entries from before this page was introduced were taken over from the existing history: requests, service log, stock movements and problem reports. For orders only their creation is known, for licenses nothing.
- A device's [service log](./devices#service-log) is unchanged: every hand-out is still listed with the single device.
:::
