from django.db import migrations, models


def copy_name(apps, schema_editor):
    """Until now the name was the manufacturer's designation."""
    AssetModel = apps.get_model("masterdata", "AssetModel")
    AssetModel.objects.update(designation=models.F("name"))


class Migration(migrations.Migration):
    dependencies = [
        ("masterdata", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="assetmodel",
            name="designation",
            field=models.CharField(
                default="",
                help_text="The model as the manufacturer calls it; unique per manufacturer.",
                max_length=150,
                verbose_name="manufacturer designation",
            ),
            preserve_default=False,
        ),
        migrations.RunPython(copy_name, migrations.RunPython.noop),
        migrations.RemoveConstraint(model_name="assetmodel", name="unique_model_name"),
        migrations.AddConstraint(
            model_name="assetmodel",
            constraint=models.UniqueConstraint(
                fields=("manufacturer", "designation"),
                name="unique_model_designation",
                violation_error_message="This manufacturer already has a model with this designation.",
            ),
        ),
    ]
