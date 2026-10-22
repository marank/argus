from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("requests", "0013_department_approval"),
    ]

    operations = [
        migrations.AddField(
            model_name="reservation",
            name="origin",
            field=models.CharField(
                choices=[("request", "Request"), ("direct", "Direct hand-out")],
                default="request",
                max_length=10,
                verbose_name="origin",
            ),
        ),
    ]
