"""Django's migrate, first switching a database over to the fresh migrations of 2026-10-22.

The migrations of Argus's own apps were replaced by new initial ones. A database from
before already has the schema they create, so this records them as applied in place of
the old ones; Django then has nothing left to do. That needs the complete old history
(the version before the switch must have migrated it). New databases and ones already
switched are left alone.
"""

from django.core.management.base import CommandError
from django.core.management.commands.migrate import Command as MigrateCommand
from django.db import connections, transaction
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.recorder import MigrationRecorder

APPS = ("accounts", "core", "masterdata", "inventory", "procurement", "requests")
# The last old migration per app; all of them must be applied before the switch.
LAST_OLD = {
    "accounts": "0016_requests_area",
    "core": "0007_request_links",
    "masterdata": "0008_category_code_optional",
    "inventory": "0011_asset_request",
    "procurement": "0003_asset_request_item",
    "requests": "0019_asset_request",
}


def switch_migration_history(connection) -> bool:
    recorder = MigrationRecorder(connection)
    if not recorder.has_table():
        return False
    on_disk = {
        key for key in MigrationLoader(None, ignore_no_migrations=True).disk_migrations if key[0] in APPS
    }
    recorded = {(row.app, row.name) for row in recorder.migration_qs.filter(app__in=(*APPS, "reservations"))}
    if not recorded - on_disk:
        return False
    if not set(LAST_OLD.items()) <= recorded:
        raise CommandError(
            "This database stems from an older Argus with migrations that no longer exist. "
            "Update it with the last version before 2026-10-22 (commit ac25933) first."
        )
    with transaction.atomic(using=connection.alias):
        recorder.migration_qs.filter(app__in=APPS).delete()
        # Only the fresh initial ones match the old schema; later migrations still have to run.
        for app, name in sorted(on_disk):
            if name.endswith("_initial"):
                recorder.record_applied(app, name)
    return True


class Command(MigrateCommand):
    def handle(self, *args, **options):
        if switch_migration_history(connections[options["database"]]):
            self.stdout.write("Switched to the fresh migrations of 2026-10-22.")
        super().handle(*args, **options)
