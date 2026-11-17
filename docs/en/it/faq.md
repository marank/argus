# FAQ

Questions from employees are answered in the [FAQ for employees](../employees/faq).

## For IT

### Why does a request not show up for me?

- It is still waiting for approval (**Awaiting approval**).
- The view is filtered, e.g. to **Open only** or to a team.
- You lack the right for **Requests & calendar**.

### Why can't I assign a device?

It is not **In stock**, belongs to a different model than the line, or is not **Loanable (pool)**. The error message states the reason.

### A request arrived without approval, although the category requires approval.

Possible reasons:

- The employee is exempt from approval.
- IT recorded the request on the employee's behalf.
- The employee is an approver of their own department.
- Neither their department nor a parent department has approvers.

### The device is already with the employee, but the request is still open.

Use **Mark as handed out** on the confirmed request. You record the devices later. See [Handing out without recorded devices](./requests#handing-out-without-recorded-devices).

### A device was stolen.

Set the status to **Lost**. A problem report "Lost or stolen" does not do this automatically. If the employee needs a replacement, use **Replace** on the stolen device; the device name passes to the replacement.

### Why does a new device get the number INV-… instead of the category's number?

The number sequence is set on a parent category. Sequences are not inherited. Set the sequence on the subcategory or on the model.

### Can I send a return reminder right away?

Yes, with **Send return reminder** on the request or in the dashboard widget **Overdue returns**.

### How do I export the device list?

There is currently no export.

### A device I just scanned was not found.

If the cursor is in an input field, the scan ends up there. Click outside it, or scan directly into the **Scan** field.

## For administrators

### A newly created user cannot sign in.

Users created in Argus have no password at first. They sign in via LDAP, or you set one under **Master data → Employees** with **Set password**.

### An employee has left the company.

Take back the devices, remove the licenses and deactivate the account. It cannot be deleted as long as it has requests; this preserves the history. Argus does not deactivate accounts automatically, not even via LDAP.

### An IT staff member sees no IT areas.

They lack a role. Only an administrator assigns roles, under **Master data → Roles** or on the employee.

### Emails do not arrive.

See [Updates and troubleshooting](./operations/maintenance#emails-do-not-arrive).

### Can I disable a module without losing data?

Yes. Disabled modules disappear from the interface; the data is kept.

### Where do I change my password?

Local accounts in the user menu under **Sign-in & security → Change password**, LDAP accounts in the directory. See [Passwords of local accounts](./administration/sign-in#passwords-of-local-accounts).
