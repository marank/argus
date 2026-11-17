# Backups

Argus sichert die Datenbank jede Nacht um `BACKUP_TIME` (Standard 01:30) in das Docker-Volume `db-backups`. Sicherungen älter als `BACKUP_KEEP_DAYS` Tage (Standard 14) werden gelöscht. Die Sicherung läuft im Container `app` mit, ein eigener Dienst ist nicht nötig.

Die Dateien heißen `<POSTGRES_DB>-<Zeitstempel in UTC>.dump`, also standardmäßig `argus-20261029T003000Z.dump`, und liegen im PostgreSQL-Custom-Format vor.

::: warning Achtung
Sicherungen auf demselben Server schützen nicht vor dem Verlust des Servers. Kopieren Sie die Dateien regelmäßig auf ein anderes System oder nehmen Sie das Docker-Volume in die Sicherung des Servers auf.
:::

## Sofort sichern

```bash
docker compose exec app python manage.py backup_database
```

## Sicherungen anzeigen und kopieren

```bash
docker compose exec app ls -l /backups
```

```bash
docker compose cp app:/backups ./backups
```

## Wiederherstellen

Die Wiederherstellung ersetzt alle aktuellen Daten. Halten Sie Argus vorher an, damit währenddessen nichts geschrieben wird.

```bash
docker compose stop app
```

```bash
docker compose exec -T db sh -c 'pg_restore --clean --if-exists --no-owner -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < backups/argus-20261029T003000Z.dump
```

```bash
docker compose start app
```

Ersetzen Sie den Dateinamen durch die gewünschte Sicherung. Beim Start spielt Argus fehlende Migrationen automatisch ein. Eine Sicherung aus einer älteren Version lässt sich deshalb auch in eine neuere Version zurückspielen.

::: tip Tipp
Testen Sie die Wiederherstellung gelegentlich auf einer separaten Instanz. Erst dann wissen Sie sicher, dass die Sicherungen brauchbar sind.
:::

::: info Gut zu wissen
- Schlägt eine Sicherung fehl, steht der Fehler im Protokoll: `docker compose logs app`.
- Mit leerem `BACKUP_DIR` in `.env` sichert Argus nicht selbst. Sichern Sie die Datenbank dann auf anderem Weg.
:::

## Umstieg vom Dienst `backup`

Frühere Versionen sicherten mit einem eigenen Dienst `backup` in das Volume `backups`. Nach dem Update entfernt dieser Befehl den alten Dienst:

```bash
docker compose up -d --remove-orphans
```

Ältere Sicherungen bleiben im Volume `argus_backups`. Kopieren Sie sie bei Bedarf heraus und löschen Sie das Volume danach:

```bash
docker run --rm -v argus_backups:/old:ro -v "$PWD/old-backups":/out alpine cp -a /old/backups/. /out/
```

```bash
docker volume rm argus_backups
```
