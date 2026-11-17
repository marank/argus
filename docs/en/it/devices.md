# Devices

**IT operations → Devices** lists all individually tracked devices: notebooks, smartphones, headsets, mobile scanners and everything else with its own inventory number.

## The list

By default the list is grouped by category. In the header you change grouping, columns and row height; **Reset view** restores the initial state.

- **Search** covers inventory number, serial number, identifier, IMEI, MAC address, device name, model, manufacturer, employee and the serial numbers of installed parts.
- **Filters** for status, category (including subcategories), model, location, employee, manufacturer, supplier, pool, purchase date and warranty end. Enter date ranges as e.g. `0611..2311`.
- **Assigned to** shows "reserved for {name}" for reserved devices.

Links from the dashboard, calendar and models open the list already filtered.

## Creating a device

There are four ways:

| Way | When |
| --- | --- |
| **New device** | A single device with all details |
| **Scan in multiple** | Many devices of one model: scan serial numbers one after another, up to 500 at once |
| **Create series** | Many identical devices without serial numbers, e.g. before delivery; serial numbers follow later |
| **Import** | Stock from an Excel or CSV file, see [Importing devices](./device-import) |

In addition, the [goods receipt](./procurement#goods-receipt) of a purchase order creates devices automatically.

### Fields

**Identification**

- **Model**: required. Only active models that are tracked as individual devices.
- **Inventory no.**: leave empty and Argus assigns the next number from the number sequence of the model or its category. Must be unique.
- **Device name**: see [Device names](#device-names).
- **Serial number**: unique per model.
- **Identifier**: a further manufacturer number, e.g. the configuration (Handtec CN, Lenovo MTM). The category determines what the field is called.
- **IMEI**, **MAC address**: The MAC address is accepted in any notation and stored as `AA:BB:CC:DD:EE:FF`.
- **Belongs to**: a parent device, e.g. the docking station of a notebook.

**Components**: If the category has replaceable parts such as batteries, you record their serial number and installation date here.

**Status & usage**: Status, condition (New, Good, Worn, Defective), location, employee, linked consumables and **Loanable (pool)**.

**Purchase & warranty**: Supplier, purchase price, purchase date, warranty end, notes.

::: info Good to know
**Loanable (pool)** is on by default. Only devices in the pool are available for requests and are allocated automatically. Switch it off for devices that should not be lent out, e.g. servers.
:::

## Status

| Status | Meaning | How it is set |
| --- | --- | --- |
| **In stock** | Available | on creation, after a return |
| **Reserved** | Allocated to a request | automatically on allocation |
| **In use** | With an employee | automatically on hand-out or assignment |
| **In repair** | Defective or being serviced | by hand, on return as defective, on replacement |
| **Lost** | Cannot be found | by hand only |
| **Retired** | Out of service | by hand or on replacement |

Every status change is recorded in the device's service log.

::: warning Caution
- A reserved device cannot be changed while it is allocated to a request. Remove it there first.
- A "Lost or stolen" problem report does not change the status. Set it to **Lost** yourself.
- When a device is retired or lost, the employee and licenses stay on the device. Remove them by hand if needed.
:::

## The device page

The device page shows all details, the model with support contacts, linked consumables, licenses and the **History**. If the device is allocated to a request or was handed out through one, a notice with a link appears at the top. Open problem reports also appear at the top.

Actions:

| Action | Purpose |
| --- | --- |
| **Take back** | Take the device back from the employee. If it was handed out through a request, it counts as returned there. |
| **Create request** | Create a request for this model (in stock only) |
| **Quick assignment** | Give the device to an employee immediately (in stock only) |
| **Replace** | Replace the device with another one from stock |
| **Record service** | Record a repair, maintenance, inspection or note |
| **Edit**, **Delete** | Change details, delete the device |

## Quick assignment

For the case "device off the shelf, straight to the employee": **Quick assignment** on a device in stock.

- Choose the **Employee**.
- **Temporary** with **Return by**, or **Permanent**.
- **Assigned from**: empty for today; an earlier date records a hand-out that has already taken place.

Argus creates a request that is handed out immediately. Temporary assignments work like any loan: with reminders, overdue status and return. The employee receives the **Handed out** notification.

Without write permission on requests, quick assignment only assigns the device, without a request.

## Device names

The **inventory number** belongs to the device forever. The **Device name** belongs to where it is used, e.g. the hostname of a PC or the name of a mobile scanner in the MDM.

- Among devices in use, each name is assigned only once. Lost and retired devices keep their name for the record but do not block it.
- The category determines whether new devices get a name automatically: **No name**, **From a number sequence** (e.g. `pc-{seq}`) or **Same as the inventory number**.
- Names are assigned automatically only on creation and only if the field is left empty.

## Replacing a device

**Replace** swaps a device for one from stock, e.g. when it is defective:

1. Choose the **Replacement**. Devices in stock from the same category are offered; with **Also from other categories**, all of them.
2. Under **This device is then**, set what happens to the old device: **In stock**, **In repair** (default) or **Retired**.
3. **Replace device**.

The replacement takes over device name, employee and location. Both devices get a service log entry referring to each other. Argus then opens the replacement.

## Service log

Every device has a **History**. **IT operations → Service log** shows all entries across all devices, with filters by type, model and period.

Argus records automatically: **Created**, **Status changed**, **Handed out**, **Returned**, **Device replaced**, **Problem reported** and **Problem resolved**.

You record by hand with **Record service**:

| Type | Example |
| --- | --- |
| **Component replaced** | Battery replacement |
| **Repair** | Display replaced |
| **Maintenance** | Cleaning, firmware update |
| **Inspection** | Electrical safety test |
| **Note** | everything else |

Each entry has a date, cost and description. For **Component replaced** and **Repair**, you also enter the part and its new serial number. For a recorded part such as the battery, the device takes over the new serial number; the old one is kept in the entry.

With **Use consumable** you book out the material used at the same time, e.g. a spare battery from stock.

Entries recorded by hand can be deleted; automatic ones cannot.

## Deleting a device

A device can only be deleted if it never appeared in a request or purchase order. Otherwise, set it to **Retired**. Deleting a device also removes its history, problem reports and license assignments.

::: tip Tip
Retire instead of deleting: that way it stays traceable who had the device and when.
:::
