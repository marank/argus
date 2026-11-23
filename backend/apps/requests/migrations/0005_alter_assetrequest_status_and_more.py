from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('requests', '0004_alter_assetrequestevent_kind'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assetrequest',
            name='status',
            field=models.CharField(choices=[('pending_approval', 'Awaiting approval'), ('submitted', 'Submitted'), ('confirmed', 'Confirmed'), ('ready', 'Ready for handover'), ('handed_out', 'Handed out'), ('completed', 'Completed'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled')], db_index=True, default='submitted', max_length=20, verbose_name='status'),
        ),
        migrations.AlterField(
            model_name='assetrequestevent',
            name='kind',
            field=models.CharField(choices=[('created', 'Requested'), ('direct', 'Direct hand-out recorded'), ('quick', 'Quick assignment recorded'), ('approved', 'Approved'), ('declined', 'Not approved'), ('confirmed', 'Confirmed'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled'), ('replaced', 'Replaced'), ('assigned', 'Assignment changed'), ('allocated', 'Allocated'), ('released', 'Allocation removed'), ('ready', 'Preparation finished'), ('reopened', 'Back in preparation'), ('rescheduled', 'Handover changed'), ('handed_out', 'Handed out'), ('returned', 'Taken back'), ('extended', 'Loan extended'), ('reminded', 'Reminded to return'), ('completed', 'Completed')], max_length=20, verbose_name='kind'),
        ),
    ]
