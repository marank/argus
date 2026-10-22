"""Django's migrate, first moving the former "reservations" app to its new label "requests".

Django cannot rename an app in a migration: it plans the run from the recorded
migrations before any of them runs. So this renames the app's tables, its recorded
migrations and content types beforehand; on a new or already moved database it does
nothing. The models are then renamed by ordinary migrations (requests 0019).
"""

from django.core.management.commands.migrate import Command as MigrateCommand
from django.db import connections, transaction

OLD_LABEL = "reservations"
NEW_LABEL = "requests"


def move_app_label(connection, old: str = OLD_LABEL, new: str = NEW_LABEL) -> bool:
    tables = connection.introspection.table_names()
    if "django_migrations" not in tables:
        return False
    quote = connection.ops.quote_name
    with transaction.atomic(using=connection.alias), connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM django_migrations WHERE app = %s", [old])
        if not cursor.fetchone()[0]:
            return False
        for table in tables:
            if table.startswith(f"{old}_"):
                cursor.execute(f"ALTER TABLE {quote(table)} RENAME TO {quote(new + table[len(old) :])}")
        cursor.execute("UPDATE django_migrations SET app = %s WHERE app = %s", [new, old])
        if "django_content_type" in tables:
            cursor.execute("UPDATE django_content_type SET app_label = %s WHERE app_label = %s", [new, old])
    return True


class Command(MigrateCommand):
    def handle(self, *args, **options):
        if move_app_label(connections[options["database"]]):
            self.stdout.write(f'Moved the app "{OLD_LABEL}" to "{NEW_LABEL}".')
        super().handle(*args, **options)
