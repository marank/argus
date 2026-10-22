import pytest
from django.core.management.base import CommandError
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

from apps.core.management.commands.migrate import APPS, LAST_OLD, switch_migration_history


def recorded():
    return set(MigrationRecorder.Migration.objects.filter(app__in=APPS).values_list("app", "name"))


def test_a_database_with_the_old_history_switches_to_the_fresh_migrations(db):
    fresh = recorded()
    MigrationRecorder.Migration.objects.filter(app__in=APPS).delete()
    for app, name in [*LAST_OLD.items(), ("requests", "0001_initial"), ("inventory", "0002_initial")]:
        MigrationRecorder.Migration.objects.create(app=app, name=name)

    assert switch_migration_history(connection)
    assert recorded() == fresh
    # Already switched: nothing left to do.
    assert not switch_migration_history(connection)


def test_an_incomplete_old_history_is_refused(db):
    MigrationRecorder.Migration.objects.create(app="requests", name="0018_quick_assignment")

    with pytest.raises(CommandError):
        switch_migration_history(connection)
