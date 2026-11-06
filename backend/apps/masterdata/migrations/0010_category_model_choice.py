"""One choice instead of the switch "any model requestable".

Categories that allowed "any model" offer any or a specific model, as before; the others
only a specific model. "Only any model" is new.
"""

from django.db import migrations, models


def forwards(apps, schema_editor):
    Category = apps.get_model("masterdata", "Category")
    Category.objects.filter(allow_any_model=False).update(model_choice="specific_only")


def backwards(apps, schema_editor):
    Category = apps.get_model("masterdata", "Category")
    Category.objects.filter(model_choice="specific_only").update(allow_any_model=False)


class Migration(migrations.Migration):
    dependencies = [("masterdata", "0009_category_identifier_label_componenttype")]

    operations = [
        migrations.AddField(
            model_name="category",
            name="model_choice",
            field=models.CharField(
                choices=[
                    ("any_or_specific", "Any or a specific model"),
                    ("any_only", "Any model only"),
                    ("specific_only", "A specific model only"),
                ],
                default="any_or_specific",
                help_text=(
                    "“Any model”: IT picks the model when handing out, e.g. a charging cable when the "
                    "type does not matter. Only any model: employees cannot pick one themselves, e.g. "
                    "for scanners. Only a specific model: e.g. toner, where the type matters."
                ),
                max_length=20,
                verbose_name="choice in the portal",
            ),
        ),
        migrations.RunPython(forwards, backwards),
        migrations.RemoveField(model_name="category", name="allow_any_model"),
    ]
