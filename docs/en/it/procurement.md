# Procurement

Procurement leads from missing devices and material to a purchase order, and from goods receipt back to the waiting request.

## Demand

**Procurement → Demand** shows what the stock does not cover. Select rows and combine them into one purchase order with **Create order**.

### From requests

Open lines of requests with the status **Submitted** or **Confirmed**:

| Column | Meaning |
| --- | --- |
| **Not allocated** | What the request is still missing |
| **In pool** | What is available in stock |
| **On order** | What has already been ordered for this line |
| **To order** | What is still missing after that |

Lines covered by the stock are hidden. You can show them, but not order them.

### Below minimum stock

Consumables whose stock is below the minimum stock, with the share already ordered.

::: info Good to know
- Requests **Awaiting approval** do not appear yet; requests that are ready for handover or further along no longer appear.
- Each line is calculated on its own. One free device can therefore make several requests appear covered at the same time.
- For "any model", only models of the category itself count, not those of its subcategories.
- Custom requests only count against the stock once a model is linked to them.
:::

## Purchase orders

**Procurement → Purchase orders** lists all purchase orders. If an expected delivery date has passed, it is highlighted.

### Status

| Status | Meaning |
| --- | --- |
| **To order** | Draft, lines can still be changed |
| **Ordered** | Ordered from the supplier |
| **Partially received** | Part of it has arrived |
| **Received** | Everything has arrived |
| **Cancelled** | Aborted |

### Creating and placing an order

1. From the demand or with **New order**.
2. Choose the **Supplier**. From the demand, the model's default supplier is preselected.
3. Check the lines: model or description, quantity, unit price. Without a price, the model's list price applies.
4. **Mark as ordered** with order date, expected delivery date and the supplier's reference.

Lines can only be changed in the status **To order**. Supplier, reference, delivery date, delivery location and notes can be changed until delivery.

### Cancelling and deleting

- **Cancel order** works for **To order** and **Ordered**, but no longer after a partial delivery.
- **Delete** works only for **To order**.

## Goods receipt

**Goods receipt** books incoming goods. Choose the storage location under **Deliver to**; it applies to all lines.

| Type | Input | Result |
| --- | --- | --- |
| **Individual devices** | Scan serial numbers, one per line. Without serial numbers, only the quantity. | New devices in stock, with supplier, purchase date today, price, and warranty end from the model's warranty period. Inventory number and device name follow the category's rules. |
| **Consumables** | Quantity | Stock at the storage location increases (movement **Goods receipt**) |
| **Software license** | Quantity | Only counted as received. You create the license under [Licenses](./licenses). |

Book partial deliveries one after another. The order then stays **Partially received** until everything has arrived.

### Directly to the waiting request

If a line belongs to a request with the status **Confirmed**, Argus allocates the delivered devices and material directly to that request. The devices are then **Reserved**, and the preparation of the request can be finished.

If the request is no longer **Confirmed**, the goods go into stock.

::: warning Caution
- Goods receipt is all or nothing. On an error, e.g. a serial number that already exists, nothing is booked.
- Lines without a model, that is with only a description, cannot be booked in. So link a model to custom requests before ordering.
:::

## Order numbers

Argus assigns order numbers from the number sequence for purchase orders, by default `PO-2026-0001`, restarting every year. See [Number sequences](./administration/master-data#number-sequences).
