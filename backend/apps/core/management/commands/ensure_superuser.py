"""Create the initial administrator from environment variables, and keep it an administrator.

Reads ADMIN_USERNAME, ADMIN_PASSWORD and optionally ADMIN_EMAIL; does nothing if the
variables are missing. Runs on every container start: an existing user of that name is
made an administrator again, but its password and whether it is active stay as they are.
The password is taken as given (no password rules); to change it later use ``set_password``.
"""

import os
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a superuser from ADMIN_* variables, or make the existing user one again."

    def handle(self, *args: Any, **options: Any) -> None:
        username = os.environ.get("ADMIN_USERNAME", "").strip()
        password = os.environ.get("ADMIN_PASSWORD", "")
        if not username or not password:
            self.stdout.write("No ADMIN_USERNAME/ADMIN_PASSWORD set, skipping.")
            return

        User = get_user_model()
        user = User.objects.filter(username=username).first()
        if user:
            if not (user.is_superuser and user.is_staff):
                user.is_superuser = user.is_staff = True
                user.save(update_fields=["is_superuser", "is_staff"])
                self.stdout.write(self.style.WARNING(f"“{username}” is an administrator again."))
            self.stdout.write(
                f"Superuser “{username}” already exists; ADMIN_PASSWORD is only used to create it "
                "(change it with `python manage.py set_password`)."
            )
            if not user.is_active:
                self.stdout.write(self.style.WARNING("The account is deactivated and cannot sign in."))
            return
        User.objects.create_superuser(
            username=username, email=os.environ.get("ADMIN_EMAIL", ""), password=password
        )
        self.stdout.write(self.style.SUCCESS(f"Superuser “{username}” created."))
