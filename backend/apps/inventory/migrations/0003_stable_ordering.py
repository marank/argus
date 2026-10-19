from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0002_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="assetevent",
            options={
                "ordering": ["-occurred_at", "-created_at"],
                "verbose_name": "asset event",
                "verbose_name_plural": "asset events",
            },
        ),
        migrations.AlterModelOptions(
            name="stockmovement",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "stock movement",
                "verbose_name_plural": "stock movements",
            },
        ),
    ]
