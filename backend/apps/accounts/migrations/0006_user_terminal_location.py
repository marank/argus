import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_department_sort_order"),
        ("masterdata", "0005_category_item_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="terminal_location",
            field=models.ForeignKey(
                blank=True,
                help_text="Pickup terminal only: lists pickups at this location and below; empty lists all.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="masterdata.location",
                verbose_name="terminal site",
            ),
        ),
    ]
