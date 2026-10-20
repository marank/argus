from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("masterdata", "0006_responsible_team"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="requires_approval",
            field=models.BooleanField(
                default=False,
                help_text="Requests must first be approved by the employee's department. Applies to the subcategories as well.",
                verbose_name="requires approval",
            ),
        ),
    ]
