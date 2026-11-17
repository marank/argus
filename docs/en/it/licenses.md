# Licenses

Under **IT operations → Licenses** you manage software licenses with seats, term and assignments.

## Creating a license

You need a model with the tracking **Software license** in a software category, e.g. “Microsoft 365 E3”.

| Field | Meaning |
| --- | --- |
| **Software** | The model |
| **Contract / reference** | Tells several licenses of the same software apart, e.g. the contract number |
| **License key** | Optional |
| **Seats** | How many assignments are possible |
| **Assigned to** | **Employees** (e.g. Microsoft 365) or **Devices** (e.g. Windows, antivirus) |
| **Valid from**, **Valid until** | An empty “Valid until” means unlimited |
| **Supplier**, **Purchase date**, **Purchase price**, **Notes** | Purchase data |

The list shows the seats in use and marks licenses as **expires soon** or **expired**.

## Assigning

On the license page, under **Assignments**, choose an employee or a device, optionally with a note, and click **Add**. With **Remove assignment** you free a seat again.

Expired licenses and licenses without free seats cannot be assigned.

Employees see their licenses in self-service under **My software**, without the license key.

## Software through requests

Employees request software in self-service, provided **Request software** is switched on in the settings. When handling the request, IT chooses a license with a free seat, see [Handling requests](./requests#software).

If you remove an assignment that came from a request, it counts as returned there.

## Expiry and warnings

If a temporary license ends within the warning period (default: 60 days), it appears:

- on the dashboard under **License ends ≤ {n} days**
- in the calendar as **License ends**
- as the notification **License ending** to IT, once per license and end date

If you extend a license by setting a new **Valid until**, Argus warns again before the new end.

## Changing and deleting

- You cannot lower the seats below the number of seats in use.
- You can only change **Assigned to** while there are no assignments.
- You can only delete a license while there are no assignments.

::: info Good to know
The goods receipt does not create ordered licenses automatically. Record them here after delivery.
:::
