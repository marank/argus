# Scanning

Argus works with any barcode scanner that types like a keyboard. No setup is needed.

## Everywhere in the IT views

A scan works on every page, even without clicking into the search field first. Alternatively, type the number into the **Scan** field at the top.

| Scanned | Result |
| --- | --- |
| Inventory number, serial number, identifier, IMEI, MAC address | The device page opens |
| Serial number of a built-in part, e.g. a battery | The page of the device the part is installed in |
| EAN or article number | The device list, filtered by the model |

If there are several matches, you choose from a list. Without a match, Argus shows “No match for …”.

::: info Good to know
- If the cursor is in an input field, the scan goes into that field.
- If a page has its own scan field, e.g. when allocating devices, scans go there.
- Argus recognizes a scan by the fast input followed by Enter. Argus does not intercept very short codes of fewer than 5 characters; type these into the scan field.
:::

## Several devices in a row

| Where | What happens |
| --- | --- |
| [Allocating devices](./requests#allocating-devices) to a request | Every scanned device goes into the matching open line. |
| [Direct hand-out](./requests#direct-hand-out) | Every scanned device goes into the cart. |
| **Devices → Scan in multiple** | Serial numbers of new devices of one model, one per scan |
| [Goods receipt](./procurement#goods-receipt) | Serial numbers of delivered devices |

When allocating devices and in the direct hand-out, Argus only recognizes inventory and serial numbers. If several devices have the same serial number, scan the inventory number.
