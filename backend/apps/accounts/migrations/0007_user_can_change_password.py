from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0006_user_theme"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="can_change_password",
            field=models.BooleanField(
                default=True,
                help_text="Local accounts change their own password under Sign-in & security. Directory accounts change it in the directory.",
                verbose_name="may change password",
            ),
        ),
    ]
