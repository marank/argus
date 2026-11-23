from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activity', '0004_alter_activity_kind'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='kind',
            field=models.CharField(choices=[('request_created', 'Requested'), ('request_direct', 'Direct hand-out recorded'), ('request_quick', 'Quick assignment recorded'), ('request_approved', 'Approved'), ('request_declined', 'Not approved'), ('request_confirmed', 'Confirmed'), ('request_rejected', 'Rejected'), ('request_cancelled', 'Cancelled'), ('request_replaced', 'Replaced'), ('request_assigned', 'Assignment changed'), ('request_allocated', 'Allocated'), ('request_ready', 'Preparation finished'), ('request_reopened', 'Back in preparation'), ('request_rescheduled', 'Handover changed'), ('request_handed_out', 'Handed out'), ('request_returned', 'Taken back'), ('request_extended', 'Loan extended'), ('request_reminded', 'Reminded to return'), ('request_completed', 'Completed'), ('asset_created', 'Device created'), ('assets_created', 'Devices created'), ('assets_imported', 'Devices imported'), ('asset_status_changed', 'Status changed'), ('asset_assigned', 'Handed out'), ('asset_returned', 'Returned'), ('asset_replaced', 'Device replaced'), ('asset_component_replaced', 'Component replaced'), ('asset_repair', 'Repair'), ('asset_maintenance', 'Maintenance'), ('asset_inspection', 'Inspection'), ('asset_note', 'Note'), ('asset_event_deleted', 'History entry deleted'), ('asset_deleted', 'Device deleted'), ('issue_reported', 'Problem reported'), ('issue_in_progress', 'Report taken into work'), ('issue_reopened', 'Report reopened'), ('issue_resolved', 'Problem resolved'), ('consumable_receipt', 'Stock received'), ('consumable_issue', 'Stock issued'), ('consumable_return', 'Stock returned'), ('consumable_adjustment', 'Stock corrected'), ('consumable_consumption', 'Stock consumed'), ('license_created', 'License created'), ('license_deleted', 'License deleted'), ('license_assigned', 'Seat assigned'), ('license_unassigned', 'Seat removed'), ('order_created', 'Order created'), ('order_placed', 'Ordered'), ('order_received', 'Delivery received'), ('order_cancelled', 'Order cancelled'), ('order_deleted', 'Order deleted')], max_length=30, verbose_name='kind'),
        ),
    ]
