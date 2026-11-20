import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest
from django.core.management import CommandError, call_command
from django.db import connections

from apps.core import tasks
from apps.core.services import backups


@pytest.fixture(autouse=True)
def database(monkeypatch):
    """Production-like connection details for pg_dump. The rest of the test database's
    settings stays: Django still uses them, e.g. when a test changes TIME_ZONE."""
    settings_dict = {
        **connections["default"].settings_dict,
        "NAME": "argus",
        "HOST": "db",
        "PORT": "5432",
        "USER": "argus",
        "PASSWORD": "secret",
    }
    monkeypatch.setattr(connections["default"], "settings_dict", settings_dict)
    return settings_dict


@pytest.fixture
def backup_dir(settings, tmp_path):
    settings.BACKUP_DIR = str(tmp_path / "backups")
    settings.BACKUP_KEEP_DAYS = 14
    return tmp_path / "backups"


@pytest.fixture
def pg_dump(monkeypatch):
    """Stands in for pg_dump: writes the file it is asked for and records the call."""
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        target = command[-1].removeprefix("--file=")
        Path(target).write_text("dump")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", run)
    return calls


def age(path, days):
    then = time.time() - days * 86400
    os.utime(path, (then, then))


def test_a_dump_is_written_under_its_final_name(backup_dir, pg_dump):
    path = backups.backup_database()

    assert path.parent == backup_dir
    assert path.name.startswith("argus-")
    assert path.suffix == ".dump"
    assert path.read_text() == "dump"
    assert list(backup_dir.glob("*.partial")) == []
    command, kwargs = pg_dump[0]
    assert command[:2] == ["pg_dump", "--format=custom"]
    assert kwargs["umask"] == 0o077
    assert kwargs["env"]["PGHOST"] == "db"
    assert kwargs["env"]["PGPASSWORD"] == "secret"


def test_a_failed_dump_leaves_no_file(backup_dir, monkeypatch):
    def fail(command, **kwargs):
        Path(command[-1].removeprefix("--file=")).touch()
        raise subprocess.CalledProcessError(1, command, "", "connection refused\n")

    monkeypatch.setattr(subprocess, "run", fail)

    with pytest.raises(backups.BackupError, match="connection refused"):
        backups.backup_database()
    assert list(backup_dir.iterdir()) == []


def test_old_dumps_and_stale_partials_are_removed(backup_dir, pg_dump):
    backup_dir.mkdir()
    old = backup_dir / "argus-old.dump"
    kept = backup_dir / "argus-recent.dump"
    stale = backup_dir / "argus-dead.dump.partial"
    running = backup_dir / "argus-running.dump.partial"
    for path in (old, kept, stale, running):
        path.write_text("x")
    age(old, 15)
    age(kept, 13)
    age(stale, 1)

    backups.backup_database()

    assert not old.exists()
    assert not stale.exists()
    assert kept.exists()
    assert running.exists()


@pytest.mark.parametrize(
    ("utc", "dumps"),
    [
        # 01:30 in Europe/Berlin: 00:30 UTC in winter, 23:30 UTC the day before in summer.
        (datetime(2026, 1, 15, 0, 30, tzinfo=UTC), True),
        (datetime(2026, 1, 15, 1, 30, tzinfo=UTC), False),
        (datetime(2026, 7, 14, 23, 30, tzinfo=UTC), True),
        (datetime(2026, 7, 15, 0, 30, tzinfo=UTC), False),
    ],
)
def test_the_job_dumps_only_in_the_hour_of_backup_time(backup_dir, pg_dump, settings, utc, dumps):
    settings.TIME_ZONE = "Europe/Berlin"
    settings.BACKUP_TIME = datetime(2026, 1, 1, 1, 30, tzinfo=UTC).time()

    tasks.backup_database(timestamp=int(utc.timestamp()))

    assert bool(pg_dump) is dumps


def test_the_job_does_nothing_without_backup_dir(settings, pg_dump):
    settings.BACKUP_DIR = ""
    settings.BACKUP_TIME = datetime(2026, 1, 1, 0, 30, tzinfo=UTC).time()

    tasks.backup_database(timestamp=int(datetime(2026, 1, 15, 0, 30, tzinfo=UTC).timestamp()))

    assert pg_dump == []


@pytest.fixture
def postgres(monkeypatch):
    monkeypatch.setattr(connections["default"], "vendor", "postgresql")


def test_the_command_dumps_now(backup_dir, pg_dump, postgres, capsys):
    call_command("backup_database")

    assert "Database dumped to" in capsys.readouterr().out
    assert len(list(backup_dir.glob("*.dump"))) == 1


def test_the_command_reports_a_failed_dump(backup_dir, postgres, monkeypatch):
    def fail(command, **kwargs):
        raise subprocess.CalledProcessError(1, command, "", "")

    monkeypatch.setattr(subprocess, "run", fail)

    with pytest.raises(CommandError, match="pg_dump exited with 1"):
        call_command("backup_database")


def test_the_command_needs_backup_dir(settings, postgres):
    settings.BACKUP_DIR = ""

    with pytest.raises(CommandError, match="BACKUP_DIR"):
        call_command("backup_database")


def test_the_command_needs_postgresql(backup_dir, monkeypatch):
    monkeypatch.setattr(connections["default"], "vendor", "sqlite")

    with pytest.raises(CommandError, match="PostgreSQL"):
        call_command("backup_database")
