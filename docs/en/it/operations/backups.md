# Backups

Argus backs up the database every night at `BACKUP_TIME` (default 01:30) into the Docker volume `db-backups`. Backups older than `BACKUP_KEEP_DAYS` days (default 14) are deleted. The backup runs inside the `app` container; no separate service is needed.

The files are named `<POSTGRES_DB>-<timestamp in UTC>.dump`, so by default `argus-20261029T003000Z.dump`, and use the PostgreSQL custom format.

::: warning Caution
Backups on the same server do not protect you against losing the server. Copy the files to another system regularly, or include the Docker volume in the server's backup.
:::

## Back up now

```bash
docker compose exec app python manage.py backup_database
```

## List and copy backups

```bash
docker compose exec app ls -l /backups
```

```bash
docker compose cp app:/backups ./backups
```

## Restore

Restoring replaces all current data. Stop Argus first so that nothing is written in the meantime.

```bash
docker compose stop app
```

```bash
docker compose exec -T db sh -c 'pg_restore --clean --if-exists --no-owner -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < backups/argus-20261029T003000Z.dump
```

```bash
docker compose start app
```

Replace the file name with the backup you want. On start, Argus applies missing migrations automatically. You can therefore also restore a backup from an older version into a newer version.

::: tip Tip
Test the restore on a separate instance from time to time. Only then do you know for sure that the backups are usable.
:::

::: info Good to know
- If a backup fails, the error is in the log: `docker compose logs app`.
- With an empty `BACKUP_DIR` in `.env`, Argus does not back up by itself. Back up the database by other means then.
:::

## Migrating from the `backup` service

Earlier versions backed up with a separate `backup` service into the volume `backups`. After the update, this command removes the old service:

```bash
docker compose up -d --remove-orphans
```

Older backups remain in the volume `argus_backups`. Copy them out if needed and then delete the volume:

```bash
docker run --rm -v argus_backups:/old:ro -v "$PWD/old-backups":/out alpine cp -a /old/backups/. /out/
```

```bash
docker volume rm argus_backups
```
