"""Set a new password for an account, e.g. an administrator who forgot theirs.

    python manage.py set_password admin                  # asks for the password
    python manage.py set_password admin --reset-two-factor

Unlike Django's ``changepassword`` any password is accepted (no password rules).
It also lifts a lock after too many failed sign-ins and, on request, switches off
the second sign-in step for someone who lost their phone and backup codes.
"""

import getpass

from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import User
from apps.accounts.services import throttle, two_factor


class Command(BaseCommand):
    help = "Set a new password for an account (any password is accepted)."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument(
            "--password", help="The new password; without it the command asks (not shown, twice)."
        )
        parser.add_argument(
            "--reset-two-factor",
            action="store_true",
            help="Also switch off the second sign-in step (app or email code, backup codes).",
        )

    def handle(self, *args, username: str, password: str | None, reset_two_factor: bool, **options):
        user = User.objects.filter(username__iexact=username).first()
        if user is None:
            raise CommandError(f"There is no account “{username}”.")
        if user.ldap_dn:
            self.stderr.write(
                f"“{user.username}” signs in through LDAP; the directory password stays what it is."
            )
        if password is None:
            password = getpass.getpass("New password: ")
            if password != getpass.getpass("New password (again): "):
                raise CommandError("The passwords do not match.")
        if not password:
            raise CommandError("The password must not be empty.")

        user.set_password(password)
        user.save(update_fields=["password"])
        throttle.clear(throttle.password_key(user.username))
        throttle.clear(throttle.code_key(user))
        if reset_two_factor:
            two_factor.disable(user)
        self.stdout.write(self.style.SUCCESS(f"New password set for “{user.username}”."))
        if two_factor.method_of(user) and not reset_two_factor:
            self.stdout.write("The second sign-in step stays on; add --reset-two-factor to switch it off.")
        if not user.is_active:
            self.stdout.write(self.style.WARNING("The account is deactivated and cannot sign in."))
