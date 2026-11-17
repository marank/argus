# Workflows at a glance

The central workflows in Argus. The details are on the linked pages.

## From request to return

| Step | Who | Status afterwards |
| --- | --- | --- |
| [Submit the request](../employees/request) | Employee | **Awaiting approval** or **Submitted** |
| [Approve](../approvers/approvals), if needed | Approver | **Submitted** |
| [Confirm](./requests#confirming) | IT | **Confirmed** |
| [Allocate devices](./requests#allocating-devices) | IT | **Confirmed**, devices reserved |
| [Mark ready for pickup](./requests#marking-ready-for-pickup) | IT | **Ready for pickup** |
| [Pick up](./terminal) or [hand out](./requests#handing-out) | Employee or IT | **Handed out** (temporary) or **Completed** (permanent) |
| [Take back](./requests#taking-back), for temporary ones | IT | **Completed** |

Shortcuts: The [direct hand-out](./requests#direct-hand-out) skips request and approval, the [quick assignment](./devices#quick-assignment) hands out a single device immediately.

## From demand to device

1. **Identify demand**: A request cannot be served from stock, or a consumable falls below its minimum stock.
2. **Create order** and **Mark as ordered**.
3. **Book the goods receipt**: Devices are created and go straight to the waiting request.

See [Procurement](./procurement).

## From problem to solution

1. **The employee reports** a problem under **My devices**. The responsible team is notified.
2. **IT starts working on it** and clarifies details via messages.
3. **Resolved**: IT or the employee closes the problem report.

If needed, the device is [replaced](./devices#replacing-a-device) or repaired. See [Reporting a problem](../employees/report-issue) and [Problem reports](./issues).

## A device over time

**In stock** → **Reserved** → **In use** → **In stock** → … → **Retired**

In between, a device can go **In repair** and then back into stock. Every step is recorded in the device's [service log](./devices#service-log).
