"""Create the initial administrator from environment variables, once.

Reads ADMIN_USERNAME, ADMIN_PASSWORD and optionally ADMIN_EMAIL. Does nothing if
the variables are missing or the user already exists, so it is safe to run on every container start.
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a superuser from ADMIN_* variables if it does not exist."

    def handle(self, *args, **options):
        username = os.environ.get("ADMIN_USERNAME", "").strip()
        password = os.environ.get("ADMIN_PASSWORD", "")
        if not username or not password:
            self.stdout.write("No ADMIN_USERNAME/ADMIN_PASSWORD set, skipping.")
            return

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(f"Superuser “{username}” already exists.")
            return
        User.objects.create_superuser(
            username=username, email=os.environ.get("ADMIN_EMAIL", ""), password=password
        )
        self.stdout.write(self.style.SUCCESS(f"Superuser “{username}” created."))
