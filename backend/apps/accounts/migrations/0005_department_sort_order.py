from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_username_ignoring_case"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="department",
            options={
                "ordering": ["sort_order", "name"],
                "verbose_name": "department",
                "verbose_name_plural": "departments",
            },
        ),
        migrations.AddField(
            model_name="department",
            name="sort_order",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Lower numbers come first; equal numbers by name.",
                verbose_name="sort order",
            ),
        ),
    ]
