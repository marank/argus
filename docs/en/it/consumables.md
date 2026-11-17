# Consumables

Under **IT operations → Consumables** you track material by quantity instead of by individual device: ink, toner, batteries, cables, accessories.

## Basic principle

Every entry is an item at one storage location. If the same toner is kept in two storage locations, these are two entries, each with its own stock.

| Column | Meaning |
| --- | --- |
| **On hand** | What is physically there. The bar turns orange when the stock falls below the minimum. |
| **Reserved** | Set aside for requests |
| **Available** | On hand minus reserved |
| **Minimum** | Below this, the item counts as running low |

## Creating a new item

1. Create the model in the [master data](./administration/master-data#models) with the tracking **Consumable (quantity)**.
2. **New consumable**: choose the model, location and minimum.
3. Record the stock with **Book in**. A new entry starts at 0.

## Booking

In the menu of each row:

| Action | What for |
| --- | --- |
| **Book in** | Incoming stock, e.g. a delivery |
| **Book out** | Outgoing stock, optionally with a recipient |
| **Adjust** | Enter a new count, e.g. after a stocktaking |
| **Movements** | The last 200 bookings with reason, recipient and note |

Booking out and adjusting downwards only affect the available quantity. Units reserved for requests are locked.

Movement types: **Goods receipt**, **Issue**, **Adjustment** and **Used for repair** (via [Record service](./devices#service-log)).

## Through requests

- When you allocate, the quantity is **reserved**. The stock stays until the hand-out takes place.
- At hand-out, the quantity is booked out, with the employee as recipient and the request number as note.
- Consumables are not expected back.
- Cancelling or removing the allocation releases the reservation.

## Compatible material

On the model, under **Compatible with**, you define which material fits which device, e.g. the ink cartridge for the printer. The link applies in both directions. You can also link material to individual devices.

Employees see compatible material for their own devices in self-service under **For your devices**.

## Low stock

- Filter **Only below minimum** in the list
- Dashboard widget **Consumables running low**
- **Procurement → Demand** lists all items running low, ready to order

An item is running low when its stock is **below** the minimum. At exactly the minimum, it does not count as low yet. There is no email warning.
