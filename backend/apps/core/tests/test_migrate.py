from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

from apps.core.management.commands.migrate import move_app_label


def test_moving_an_app_label_renames_tables_and_records(db):
    """An app under its old label gets its tables and recorded migrations moved once."""
    with connection.cursor() as cursor:
        cursor.execute("CREATE TABLE oldapp_thing (id integer PRIMARY KEY)")
        cursor.execute("INSERT INTO oldapp_thing (id) VALUES (7)")
    MigrationRecorder.Migration.objects.create(app="oldapp", name="0001_initial")

    assert move_app_label(connection, "oldapp", "newapp")

    tables = connection.introspection.table_names()
    assert "newapp_thing" in tables and "oldapp_thing" not in tables
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM newapp_thing")
        assert cursor.fetchall() == [(7,)]
    assert MigrationRecorder.Migration.objects.filter(app="newapp", name="0001_initial").exists()
    # Already moved: nothing left to do.
    assert not move_app_label(connection, "oldapp", "newapp")
