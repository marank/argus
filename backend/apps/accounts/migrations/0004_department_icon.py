from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_department_parent"),
    ]

    operations = [
        migrations.AddField(
            model_name="department",
            name="icon",
            field=models.CharField(
                choices=[
                    ("building", "Building"),
                    ("briefcase", "Management"),
                    ("users", "Team"),
                    ("monitor", "IT"),
                    ("cart", "Sales"),
                    ("store", "Store"),
                    ("headset", "Customer service"),
                    ("megaphone", "Marketing"),
                    ("calculator", "Accounting"),
                    ("truck", "Logistics"),
                    ("warehouse", "Warehouse"),
                    ("wrench", "Technical services"),
                ],
                default="building",
                max_length=20,
                verbose_name="icon",
            ),
        ),
    ]
