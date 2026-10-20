from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0008_issue_assignment"),
    ]

    operations = [
        migrations.AddField(
            model_name="assetissue",
            name="unseen_update",
            field=models.BooleanField(default=False, verbose_name="unseen update"),
        ),
    ]
