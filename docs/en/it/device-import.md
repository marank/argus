# Importing devices

**Devices → Import** takes devices from an Excel or CSV file, e.g. an export from the MDM or an old inventory list. The import creates new devices and updates existing ones.

## 1. File

Supported are `.xlsx`, `.xlsm`, `.csv` and `.txt` with up to 2000 rows.

- **Excel:** If there are several sheets, choose the right one.
- **CSV:** Argus detects the delimiter (comma, semicolon, tab, vertical bar) and the encoding by itself.
- **Without column names:** If the file starts with data right away, switch off **First row holds the column names**. Argus usually detects this by itself. The columns are then called “Column 1 · first value” and so on.

Old `.xls` files and password-protected files cannot be read. Save them in Excel as `.xlsx` without a password, or as CSV.

## 2. Assign columns

Assign the matching column to each device field. Argus suggests assignments based on common column names in German and English, e.g. “Serial number”, “Seriennummer”, “SN”, “Hostname” or “Asset Tag”.

You can import: Inventory no., Serial number, Identifier, IMEI, MAC address, Device name, Model, Status, Condition, Location, Assigned to (the employee), Supplier, Purchase date, Purchase price, Warranty until and Notes.

### New devices

Here you set values for new devices that the file does not contain: model, location, status and condition. Existing devices keep their values.

The **Model** is required, either as a column or as a default for all.

### Devices already in the inventory

- **Recognize by**: how Argus recognizes an existing device, by default by the serial number. Alternatively by inventory no., IMEI, MAC address, device name, or **Not at all**, in which case every row is a new device.
- **When found**: **Update with the values of the file** or **Leave unchanged** for existing devices.
- **Ignore upper and lower case**: when recognizing devices.

::: tip Tip
Argus remembers the assignment for files with the same columns. The next time you export from the same system, everything is already assigned. The assignment is stored per browser.
:::

## 3. Preview

**Show preview** runs the complete import without saving anything. You see the result for every row:

| Result | Meaning |
| --- | --- |
| **New** | The device is created, with the inventory number it will get |
| **Update** | An existing device is changed, shown as “old → new” |
| **Unchanged** | No change |
| **Skipped** | An existing device that is to stay unchanged |
| **Error** | The row is not imported, with the reason |

If there are errors, the preview shows those rows first. Correct the file or the assignment and check again, or import only the rows without errors.

With **Import {n} devices** you apply the result.

## How Argus reads values

- **Model:** name, manufacturer designation, article number or EAN, also “Manufacturer Name” in one cell, e.g. “Handtec HT60”.
- **Employee:** username, email, “Last name, First name” or “First name Last name”.
- **Location, supplier:** name, for locations also the short code.
- **Status, condition:** the English or German label, e.g. “In stock” or “Im Lager”, or the internal value such as `in_stock`.
- **Date:** e.g. `2026-03-31`, `31.03.2026` or `31.03.26`. A time after it is ignored.
- **Price:** `1.234,56` and `1,234.56`.
- **Empty cells** and placeholders such as `-` or `--` never overwrite an existing value.

::: info Good to know
- Every row goes through the same checks as the form. An employee in the file sets the device to **In use**; Argus assigns device names according to the category's rules.
- You cannot import the parent device, the pool flag, consumables or components.
- If Argus finds a value more than once, e.g. the same serial number for two models, it narrows the match down by the row's model. If it stays ambiguous, the row is an error.
:::
