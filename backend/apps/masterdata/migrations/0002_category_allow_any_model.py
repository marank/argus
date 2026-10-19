from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("masterdata", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="allow_any_model",
            field=models.BooleanField(
                default=True,
                help_text="Employees may request “any device” of this group. Turn off where only a specific model makes sense, e.g. accessories or consumables.",
                verbose_name="any model requestable",
            ),
        ),
    ]
