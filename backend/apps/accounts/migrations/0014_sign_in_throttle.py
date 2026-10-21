import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0013_role"),
    ]

    operations = [
        migrations.CreateModel(
            name="SignInThrottle",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("key", models.CharField(max_length=200, unique=True)),
                ("failures", models.PositiveIntegerField(default=0)),
                ("window_start", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
        ),
    ]
