import uuid

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_department_icon"),
    ]

    operations = [
        migrations.AlterField(
            model_name="backupcode",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="department",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="ldapsettings",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="role",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        # Integer to UUID key: recreate the table instead of converting it. The counts
        # only live for a 15-minute window, so starting from zero loses nothing.
        migrations.DeleteModel(name="SignInThrottle"),
        migrations.CreateModel(
            name="SignInThrottle",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid7,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("key", models.CharField(max_length=200, unique=True)),
                ("failures", models.PositiveIntegerField(default=0)),
                ("window_start", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
            options={"abstract": False},
        ),
        migrations.AlterField(
            model_name="team",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="twofactor",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
    ]
