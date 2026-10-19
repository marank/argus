import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="NumberSequence",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="created at")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="updated at")),
                ("code", models.SlugField(unique=True, verbose_name="code")),
                ("name", models.CharField(max_length=100, verbose_name="name")),
                ("prefix", models.CharField(blank=True, max_length=20, verbose_name="prefix")),
                (
                    "pattern",
                    models.CharField(default="{prefix}{seq}", max_length=100, verbose_name="pattern"),
                ),
                ("padding", models.PositiveSmallIntegerField(default=5, verbose_name="padding")),
                ("next_value", models.PositiveIntegerField(default=1, verbose_name="next value")),
                (
                    "reset_period",
                    models.CharField(
                        choices=[("never", "Never"), ("yearly", "Yearly"), ("monthly", "Monthly")],
                        default="never",
                        max_length=10,
                        verbose_name="reset period",
                    ),
                ),
                (
                    "period_key",
                    models.CharField(
                        blank=True, editable=False, max_length=10, verbose_name="current period"
                    ),
                ),
            ],
            options={
                "verbose_name": "number sequence",
                "verbose_name_plural": "number sequences",
                "ordering": ["name"],
            },
        ),
    ]
