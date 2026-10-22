from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("masterdata", "0002_model_designation"),
    ]

    operations = [
        migrations.AlterField(
            model_name="category",
            name="allow_any_model",
            field=models.BooleanField(
                default=True,
                help_text="Employees may request “any model” of this category, e.g. a charging cable when the type does not matter; IT picks the model when assigning. Turn off where employees have to choose a specific model.",
                verbose_name="any model requestable",
            ),
        ),
    ]
