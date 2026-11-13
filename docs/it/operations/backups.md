# Backups

Bei der [Installation aus dem Repository](./installation#aus-dem-repository-bauen) sichert der Dienst `backup` die Datenbank jede Nacht um `BACKUP_TIME` (Standard 02:30) in das Docker-Volume `backups`. Sicherungen älter als `BACKUP_KEEP_DAYS` Tage (Standard 14) werden gelöscht.

Die Dateien heißen `<POSTGRES_DB>-<Zeitstempel in UTC>.dump`, also standardmäßig `argus-20261029T013000Z.dump`, und liegen im PostgreSQL-Custom-Format vor.

::: warning Achtung
Sicherungen auf demselben Server schützen nicht vor dem Verlust des Servers. Kopieren Sie die Dateien regelmäßig auf ein anderes System oder nehmen Sie das Docker-Volume in die Sicherung des Servers auf.
:::

## Sofort sichern

```bash
docker compose exec backup sh /backup.sh now
```

## Sicherungen anzeigen und kopieren

```bash
docker compose exec backup ls -l /var/lib/postgresql/backups
```

```bash
docker compose cp backup:/var/lib/postgresql/backups ./backups
```

## Wiederherstellen

Die Wiederherstellung ersetzt alle aktuellen Daten. Halten Sie Argus vorher an, damit währenddessen nichts geschrieben wird.

```bash
docker compose stop app
```

```bash
docker compose exec -T backup sh -c 'pg_restore --clean --if-exists --no-owner -d "$PGDATABASE"' < backups/argus-20261029T013000Z.dump
```

```bash
docker compose start app
```

Ersetzen Sie den Dateinamen durch die gewünschte Sicherung. Beim Start spielt Argus fehlende Migrationen automatisch ein. Eine Sicherung aus einer älteren Version lässt sich deshalb auch in eine neuere Version zurückspielen.

::: tip Tipp
Testen Sie die Wiederherstellung gelegentlich auf einer separaten Instanz. Erst dann wissen Sie sicher, dass die Sicherungen brauchbar sind.
:::

## Ohne Backup-Dienst

Bei der [Installation mit fertigem Image](./installation#mit-fertigem-image) läuft der Dienst `backup` nicht. Sichern Sie die Datenbank dann selbst, z. B. täglich per Cron auf dem Server:

```bash
docker compose exec -T db sh -c 'pg_dump --format=custom -U "$POSTGRES_USER" "$POSTGRES_DB"' > /var/backups/argus-$(date +%F).dump
```

Wiederherstellen wie oben, mit `docker compose exec -T db` statt `backup` und `-U "$POSTGRES_USER" -d "$POSTGRES_DB"` statt `-d "$PGDATABASE"`.
