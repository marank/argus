from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_uuid7_ids"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="theme",
            field=models.CharField(
                choices=[
                    ("system", "System"),
                    ("light", "Light"),
                    ("dark", "Dark"),
                    ("solarized", "Solarized"),
                    ("retro", "Retro"),
                ],
                default="system",
                max_length=10,
                verbose_name="theme",
            ),
        ),
    ]
