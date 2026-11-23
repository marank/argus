# Pickup terminal

The pickup terminal is a shared touch PC where employees check prepared devices and sign for the handover.

## Ways to use it

| Use | Process |
| --- | --- |
| **Handover with IT** | The employee and IT go through the pickup together at the terminal. IT explains the devices, both check them, the employee signs. |
| **Self-service pickup** | The employee collects the prepared devices alone, e.g. from a pickup shelf, and signs without IT. |

The process at the terminal is the same in both cases. In a handover with IT, the IT staff member selects themselves as the person handing out under **Change** in the last step if someone else prepared the request.

## Setup

1. Under **Master data → Employees**, create an account for the terminal, enable **Pickup terminal**, switch off **May change password** and enter a longer **Session duration (hours)**.
2. Optionally choose a location under **Terminal site**. The terminal then shows only pickups at this location and the locations below it. Without a location, it shows all.
3. Give the account a password, see [Passwords of local accounts](./administration/sign-in#passwords-of-local-accounts).
4. Sign in on the touch PC with this account.

A terminal account sees only the pickups, no other areas of Argus, and receives no notifications. IT staff can also open the terminal for testing.

::: warning Caution
By default, a sign-in is valid for 12 hours. So that the terminal does not have to be signed in again every day, enter a longer **Session duration (hours)** on the terminal account, e.g. 168 for one week.
:::

The **Pickup terminal** module must be switched on in the [Settings](./administration/settings).

## Which pickups appear

The terminal lists all requests that are **Ready for handover** and have **Pickup with signature** as their handover type. The next pickup is at the top. The list updates itself.

You can search by name or request number; tapping the name starts the pickup.

## Process

### 1. Check devices

The employee sees all devices and items of the request, with the return date or **Permanent**. If IT has left a remark, it appears here.

If something is not right, e.g. visible damage, the employee records a note per device with **Add note**. **Further remarks** has room for everything else. Continue with **Everything checked**.

If IT skipped the device check, the terminal starts with step 2.

### 2. Who collects?

- **I am {name}**: The employee collects the devices themselves.
- **Someone else**: A colleague collects on their behalf. The colleague searches for themselves by name or employee number. If they are not found, the name entered is used.

In every case, the devices are assigned to the employee who requested them.

### 3. Sign

The terminal shows who receives the devices and who from IT hands them out. The person who finished the preparation is suggested; with **Change** you can select someone else from IT. The person selected here appears in the record.

The employee signs in the field and taps **Sign and finish**. The request is then handed out; the employee receives a confirmation.

::: info Good to know
- After 2 minutes without input, the terminal returns to the list. Entries already made are lost.
- **Cancel** discards a pickup in progress after a confirmation prompt.
- Licenses do not appear in the device check; they are still handed over with the pickup.
:::

## Handover record

Every handover has a record in A4 format. IT opens it on the request from the **Handover** card and prints it with **Print**.

The record contains:

- employee, department, purpose and period
- handover type, recipient, person handing out and the recording account (e.g. the terminal)
- all devices with inventory number, model, serial number and notes
- the signature; for a hand-out without the terminal, an empty signature line
- later returns with defect remarks

Employees see the handover on their request; only IT sees the record itself.
