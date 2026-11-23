# Master data

Under **Master data** you maintain the foundations everything else builds on. The [roles](./roles) determine who may see and change which master data.

## General

- Clicking a row opens the form. **Create + New** saves and directly opens an empty form for the next entry.
- Categories, locations and departments can be shown hierarchically with **As tree**.
- An entry that is still in use cannot be deleted. Set it to inactive instead, where the **Active** field exists.
- Selection lists in forms also work for users who are not allowed to see a master data area themselves.

## Recommended order

For a new instance:

1. Check [number sequences](#number-sequences)
2. [Locations](#locations) with storage locations and pickup points
3. [Departments](#departments)
4. IT [teams](#teams)
5. [Manufacturers](#manufacturers) and [suppliers](#suppliers)
6. [Categories](#categories)
7. [Models](#models)
8. [Employees](#employees), if they do not come from LDAP

## Manufacturers

Name, website, and support address and phone. The support contacts appear on every device page.

A manufacturer with models cannot be deleted.

## Suppliers

Name, customer number and contact details. Inactive suppliers are not offered when ordering from demand.

A supplier with purchase orders cannot be deleted.

## Categories

Categories group models, e.g. "Notebooks" or "Headsets", and control a lot of behavior.

| Field | Meaning |
| --- | --- |
| **Name (plural)** | e.g. "Notebooks" |
| **Singular name** | In self-service as "Notebook · any model" |
| **Type** | **Hardware** or **Software**. Subcategories have the same type as their parent. |
| **Parent** | For subcategories |
| **Name of the identifier** | What the "Identifier" field is called on devices, e.g. "CN" |
| **Number sequence** | For the inventory numbers of new devices |
| **Name of new devices** | **No name**, **From a number sequence** or **Same as the inventory number**, see [Device names](../devices#device-names) |
| **Responsible team** | Receives requests and problem reports for this category |
| **Requestable in portal** | Appears in self-service |
| **Choice in the portal** | **Any or a specific model**, **Any model only** or **A specific model only** |
| **Requires approval** | Requests need the department's approval |
| **Accessories** | Appears in self-service as an accessory for matching models |

### What subcategories inherit

| Setting | Inherited? |
| --- | --- |
| Requires approval | Yes |
| Accessories | Yes |
| Responsible team | Yes, unless the subcategory has its own |
| Components | Yes |
| Number sequence | **No** |
| Name of new devices | **No** |
| Name of the identifier | **No** |

::: warning Caution
Number sequences are not inherited. A subcategory without its own sequence gets numbers from the general inventory sequence (`INV-000001`). So set the sequence on every category that contains devices, or directly on the model.
:::

### Components

Under **Master data → Components** you create replaceable parts, e.g. "Battery", and assign them to categories. Devices in these categories and their subcategories then get fields for the part's serial number and installation date.

## Models

| Field | Meaning |
| --- | --- |
| **Name**, **Manufacturer designation**, **Manufacturer**, **Category** | Required. The manufacturer designation is unique per manufacturer. |
| **Tracking** | **Individual devices**, **Consumable (quantity)** or **Software license**. Software categories contain only licenses. |
| **Part number**, **EAN / GTIN** | Scanning these numbers finds the model. |
| **Number sequence** | For inventory numbers; takes precedence over the category's sequence |
| **Default supplier**, **List price** | Prefilled when ordering |
| **Warranty (months)** | Warranty end at goods receipt (default 24) |
| **Responsible team** | Takes precedence over the category's team |
| **Requestable in portal** | Appears in self-service |
| **Successor of** | Links model generations |
| **Compatible with** | Matching accessories and consumables, in both directions |

**Create successor** (in a row's menu) creates a new model and copies manufacturer, category, tracking, number sequence, supplier, warranty, team, portal setting and compatibility.

A model that has devices, stock, licenses, purchase orders or requests cannot be deleted. Set it to inactive.

## Locations

Locations form a hierarchy, e.g. "Munich / Building A / Room 2.14". **Kind**: **Site**, **Building**, **Room** or **Storage**.

**Pickup point** makes a location selectable as the pickup point when finishing the preparation of a request.

A location with sublocations or consumable stock cannot be deleted.

## Departments

Departments also form a hierarchy. The most important field is **Approvers**: they approve the department's requests. For their absence, approvers enter a [delegate](../../approvers/delegation) themselves; IT does not need to change anything. An administrator sees all delegations in the Django admin.

If a department has no approvers of its own, those of the next higher department apply. The list shows them with the note "Taken over from the parent department".

::: warning Caution
If there is no approver anywhere in the hierarchy, requests that require approval go straight to IT without any notice.
:::

## Teams

Teams divide IT, e.g. "Workplace" and "Mobile devices". Categories and models refer to a **responsible team**; new requests and problem reports then go to that team.

- **Members**: IT staff only
- **Default team**: receives everything no other team is responsible for. There is at most one.
- **LDAP group**: With LDAP, Argus syncs the members with this group at every sign-in.

## Employees

| Section | Fields |
| --- | --- |
| **Person** | First name, last name, email, phone |
| **Organisation** | Department, position, personnel number, **Exempt from approval** |
| **Account** | Username, active, **May change password**, **Session duration (hours)**, set password, reset two-factor sign-in |
| **Permissions** | **IT staff**, **Administrator**, teams, roles |
| **Pickup terminal** | Account for the [pickup terminal](../terminal) and its location |

The **Account** column shows flags such as **Admin**, **IT**, **Terminal**, **LDAP** and **2FA**.

::: info Good to know
- Users created in Argus have no password at first. They sign in via LDAP, or an administrator sets one with **Set password** in the **Account** section, see [Passwords of local accounts](./sign-in#passwords-of-local-accounts).
- Employees with requests or assigned devices cannot be deleted. Deactivate them instead; they can then no longer sign in.
- Nobody can deactivate or delete their own account, and nobody can remove their own administrator rights.
:::

## Number sequences

Argus assigns consecutive numbers from number sequences: inventory numbers, device names, request numbers and purchase order numbers.

| Field | Meaning |
| --- | --- |
| **Prefix** | Inserted for `{prefix}` |
| **Pattern** | Structure of the number, e.g. `{prefix}{year}-{seq}` |
| **Digits** | Minimum length of the sequential number, padded with zeros |
| **Restart** | **Never**, **Yearly** or **Monthly** |
| **Next value** | The next sequential number |

Placeholders in the pattern:

| Placeholder | Result |
| --- | --- |
| `{prefix}` | The prefix |
| `{year}` | Year, four digits |
| `{yy}` | Year, two digits |
| `{month}` | Month, two digits |
| `{seq}` | Sequential number (required) |

The preview in the form shows example numbers.

### System sequences

Three sequences belong to Argus itself; you can change them but not delete them:

| Sequence | Default | Example |
| --- | --- | --- |
| Inventory numbers | `INV-{seq}`, 6 digits | `INV-000042` |
| Requests | `RES-{year}-{seq}`, 5 digits, restarts yearly | `RES-2026-00017` |
| Purchase orders | `PO-{year}-{seq}`, 4 digits, restarts yearly | `PO-2026-0003` |

### Custom sequences

You assign custom sequences to:

- a **category** or a **model** for inventory numbers, e.g. `NB-{seq}` for notebooks
- a **category** under **Name of new devices** for device names, e.g. `pc-{seq}` or `H{seq}`

::: info Good to know
- Argus skips numbers that are already taken, e.g. after a manual entry.
- With a yearly or monthly restart, counting starts again at 1 with the first number in the new period.
- A sequence that a category uses for device names cannot be deleted.
:::
