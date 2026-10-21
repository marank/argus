from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0014_sign_in_throttle"),
        ("core", "0003_notifications_and_rules"),
        ("masterdata", "0007_category_requires_approval"),
    ]

    operations = [
        migrations.AlterField(
            model_name="category",
            name="code",
            field=models.SlugField(blank=True, max_length=30, verbose_name="code"),
        ),
        migrations.AddConstraint(
            model_name="category",
            constraint=models.UniqueConstraint(
                condition=models.Q(("code", ""), _negated=True),
                fields=("code",),
                name="unique_category_code",
                violation_error_code="unique",
                violation_error_message="A category with this code already exists.",
            ),
        ),
    ]
