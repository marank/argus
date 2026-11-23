# Handling requests

Under **IT operations → Requests**, IT handles all requests: confirming them, allocating devices, planning the handover, handing out and taking back.

## Workflow at a glance

| Status | What IT does |
| --- | --- |
| **Awaiting approval** | Nothing. The department decides first. |
| **Submitted** | Review, then **Confirm** or **Reject**. |
| **Confirmed** | Allocate devices, order what is missing, then **Finish preparation**. |
| **Ready for handover** | Let the employee collect the devices at the terminal, or **Hand out**. |
| **Handed out** | On return, **Take back**; if needed, **Extend loan**. |
| **Completed** | Nothing more. Permanent hand-outs can still be taken back. |

Every request shows under **Next step** what to do next. Rare actions are under **More actions** (⋮).

## The list

By default the list shows **Open only** requests. Other views: **Overdue** and **All**. You can filter by status, duration, department, team, assignee and start date.

The **Pickup** column shows the agreed date. **Preferred** means there is only the employee's preferred date; **passed** means the date is in the past.

## Responsibility

Every request has a **Team** and optionally an **Assignee**. New requests go automatically to the team of the first model or its category, otherwise to the default team. That team receives the notifications about new requests; without a team, all of IT does.

Change the team and assignee in the **Responsible** card and apply both with **Save**. **Assign to me** makes a request yours right away, without saving. If you assign it to someone else, that person receives a notification. Employees do not see who is responsible.

## Confirming

**Confirm** opens a dialog showing the availability of each line in the requested period.

- If the stock does not cover a line, reduce the quantity. A quantity of 0 removes the line.
- Under **Comment from IT** you can leave the employee a message.

The employee receives a notification. When and where they get the devices is set later, when you finish the preparation.

While the request is **Confirmed**, you change the quantities with **Edit**. A quantity cannot go below the number of devices already allocated. The employee is not notified again.

## Rejecting and cancelling

- **Reject** (when Submitted or Confirmed) requires a reason for the employee.
- **Cancel request** (under ⋮) is possible until the devices are handed out. Allocated devices go back to the pool.

The employee is notified in both cases.

## Replacing

If the employee needs something else or more afterwards, replace the request as long as it is not handed out: **Replace** (under ⋮) opens the cart with the request's details and lines, for a direct hand-out with its devices. Change what is needed and send it.

- The old request is cancelled; its history shows **Replaced** with the new number. The employee gets no email.
- The new request shows **Follows** with the old number and keeps who is responsible and the planned handover.
- If the old request was confirmed, so is the new one. Allocated devices move to the matching new line; whatever no longer fits goes back to the pool.
- The approval carries over: if the old request was waiting for the department, the new one waits too and the approvers are notified. If it was already approved, the new one stays approved. A waiting request cannot be replaced by a direct hand-out.
- For a direct hand-out the cart names what it cannot take over (devices still missing on a line, license seats); pick them again if needed.
- IT gets no notification about a new request.

::: info Good to know
Cancelling only happens on sending. If you leave the cart, the request stays as it is.
:::

## Custom requests

Lines that are not in the catalog are marked as **Custom request**. Before you allocate devices, decide:

- **Create model**: creates the model in the master data and links it.
- **Existing model…** → **Assign**: links an existing model.
- Set the quantity to 0 when confirming if the request is dropped.

## Allocating devices

After confirming, you allocate specific devices to each line. The progress is shown at the top, e.g. "3 of 5 ready".

- **Scan:** Scan the inventory or serial number. Argus places the device in the matching open line automatically. A line for exactly this model takes precedence over an "any model" line.
- **By hand:** In a line, pick a device from the list of matching devices in stock.
- **Automatically:** **Automatically** fills one line, **Allocate all automatically** the whole request. Argus takes devices in the best condition first. Custom requests stay open.

Allocated devices have the status **Reserved** and are no longer available for other requests. To remove an allocation, use the round button on the line.

Next to each allocated device is who allocated it; hover over it to see when. This way several people from IT can prepare one request together.

### Consumables

You tick off consumables (**Tick off as set aside**). The whole quantity comes from **one** storage location. If several locations are available, choose one. If no single location has enough, Argus reports "Not enough in stock".

Consumables are booked out on hand-out and are not expected back.

### Software

For software lines, choose a license with free seats under **Choose license…**. For device licenses, you also choose a device that belongs to the employee.

The license seat is assigned immediately, not on hand-out. Automatic allocation uses only user licenses and prefers the license that expires first.

If there is no free license, create one or increase the seats under [Licenses](./licenses).

### Ordering missing devices

If the stock is not enough, **Order missing** creates a purchase order for the open lines. On goods receipt, the delivered devices are allocated directly to this request, see [Procurement](./procurement).

## Finishing the preparation

Once all lines are allocated, **Finish preparation** completes the preparation and plans the handover. The request is then **Ready for handover**.

| Handover type | Process |
| --- | --- |
| **Simple pickup** | The employee collects the devices without signing. IT then records under **Hand out** who received them. |
| **Pickup with signature** | The employee collects the devices at the [pickup terminal](./terminal) and signs there. |
| **Delivered by IT** | IT brings the devices over and then records the hand-out. |

You also set the date, time and **Pickup location**; for a delivery, only the date. The employee's preferred date is shown in the dialog.

::: info Good to know
The next full hour is suggested. You choose the time in the field next to the date, in quarter hours between 6:00 and 20:00. If there is only one pickup location, it is already filled in.
:::

- **Notify the employee**: The employee receives the date and place. This requires a date and a place. For a direct hand-out, this option is off by default.
- **Skip the device check at the terminal**: The terminal starts directly with "Who collects?".

Whoever finishes the preparation is shown as **Prepared by** on the request and is suggested at the terminal as the person handing out.

You change date, place and type later with **Change handover** (under ⋮). If the request is already **Ready for handover** and notification is switched on, the employee is told about the change.

**Back to preparation** (under ⋮) takes the request off the pickup terminal. The allocated devices stay allocated.

::: info Good to know
- If you remove an allocation from a request that is **Ready for handover**, it goes back to **Confirmed**.
- If the request contains only software, the button is called **Release licenses**. The request then counts as handed out immediately.
:::

## Handing out

**Hand out** records a handover by IT, without a signature:

- **Received by**: the employee by default, otherwise a colleague
- **Delivered to**: for deliveries, e.g. "Room 2.14"
- **Notes per device** and **Notes**, e.g. "Scratch on the lid"

The devices always belong to the employee who requested them afterwards, even if a colleague receives them.

After the hand-out:

- Temporary requests are **Handed out** until everything is back.
- Permanent requests are **Completed** immediately.
- Requests with only consumables are **Completed** immediately.

Every handover has a printable **Handover record**. You open it from the **Handover** card.

## Handing out without recorded devices

Sometimes devices are already with the employee before IT has recorded them in Argus. For this, confirmed requests offer **Mark as handed out**:

- Devices already allocated are handed out normally.
- Open lines stay open. The request then shows **Record devices**.
- A device recorded later counts as being with the employee since the original hand-out.
- The employee receives no notification.

If the devices come back without having been recorded, **Mark as returned** closes the open lines. After that, no more devices can be recorded.

## Extending the loan

For temporary requests that are handed out, **Extend loan** moves the return date by 1, 2 or 4 weeks or to a date of your choice. The maximum loan period does not apply. The employee is notified.

## Taking back

**Take back** opens the **Return** dialog:

1. Select the returned lines.
2. If needed, note the condition, e.g. "Display cracked".
3. Mark defective devices as **Damaged**. They go to **In repair** instead of **In stock**.

Partial returns are possible. Each return is recorded separately with date and person. License seats are released on return. Once everything is back, the request is **Completed**.

If you take back a device on its device page, that also counts as a return on the request.

## Overdue returns

A temporary request is overdue when the return date has passed. It is then shown in red, in the **Overdue** filter, on the dashboard and in the calendar.

Argus reminds the employee automatically:

- **Return reminder**: a few days before (default: 2 days, see [Settings](./administration/settings#deadlines-warnings))
- **Return overdue**: once, as soon as the date has passed

Each is sent only once per return date. After an extension, Argus reminds again.

In addition, **Send return reminder** emails the employee immediately. It is sent even if they have switched off notifications. This requires email sending to be set up and an email address for the employee.

## Requesting on behalf of an employee

Under **New request** you request devices from the catalog, for yourself or, under **Request for employee**, on behalf of someone else. If IT creates a request for someone else, no approval is needed.

To provide specific devices from stock, use the [direct hand-out](#direct-hand-out).

## Direct hand-out

Under **IT operations → Direct hand-out** (or **Hand out directly** in the requests), you provide specific devices from stock to an employee, without a request and without approval. The menu entry only appears with write permission on requests.

1. Scan or search devices, add consumables.
2. Choose the employee, duration and period.
3. The request is created directly as **Confirmed**, with all devices allocated.
4. Continue as usual with **Finish preparation** and **Hand out**, or at the terminal.

In the list, direct hand-outs carry the badge **direct**.

## Quick assignment

The fastest option for a single device: **Quick assignment** on the page of a device in stock. The device is handed out immediately, see [Devices](./devices#quick-assignment).

## History

The **History** of a request shows every step with date and person: approval, confirmation, allocations, finishing the preparation, hand-out, extensions, reminders and returns. Employees see only the entries relevant to them.

The entry **Preparation finished** lists the devices. If people other than the one who finished it allocated devices, it says who allocated which, e.g. "Allocated by Anna Smith: NB-0012".

Every single allocation and removal, also during the preparation, is in the [detailed history](./activities#detailed-history): the link at the top right of the **History** card.

::: info Good to know
- If Argus reports "This is not possible while the request is …", a colleague has usually edited the request at the same time. Reload the page.
- Employees can cancel a request as long as it has not been handed out, even when it is already ready for handover.
:::
