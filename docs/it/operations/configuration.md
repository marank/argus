# Konfiguration

Argus wird über Umgebungsvariablen in der Datei `.env` im Projektverzeichnis konfiguriert. Nach einer Änderung übernimmt `docker compose up -d` die neuen Werte.

Einstellungen, die sich im laufenden Betrieb ändern (Module, Fristen, E-Mail-Server), liegen nicht hier, sondern unter [Einstellungen](../administration/settings) in Argus.

## Anwendung

| Variable | Standard | Bedeutung |
| --- | --- | --- |
| `ARGUS_IMAGE` | `argus:latest` | Das Image, das läuft. Standard ist das lokal aus dem Repository gebaute. Für ein fertiges Image z. B. `ghcr.io/marank/argus:1`, siehe [Installation](./installation#mit-fertigem-image). |
| `APP_URLS` | `http://localhost:8080` | Alle Adressen, unter denen Argus aufgerufen wird, kommagetrennt. Daraus leitet Argus erlaubte Hosts, CSRF-Ursprünge und sichere Cookies ab. |
| `APP_PORT` | `8080` | Port auf dem Host |
| `APP_WORKERS` | 2 × CPU + 1, höchstens 5 | Anzahl der Gunicorn-Prozesse |
| `APP_DEMO_DATA` | `false` | `true` füllt eine Datenbank ohne Geräte mit Demodaten |
| `TRUSTED_PROXIES` | leer | IP-Adressen oder CIDR-Bereiche des TLS-Proxys, kommagetrennt |
| `SECRET_KEY` | – | Pflicht. Zufallswert mit mindestens 40 Zeichen, kein Platzhalter wie `change-me` |
| `TIME_ZONE` | `Europe/Berlin` | Zeitzone für Termine, Erinnerungen und Backups |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING` oder `ERROR` |
| `DEBUG` | `false` (mit `SECRET_KEY`) | Nur für die Entwicklung. Schaltet u. a. die API-Dokumentation unter `/api/docs` frei. |

::: warning Achtung
Jede Adresse, unter der Argus aufgerufen wird, muss in `APP_URLS` stehen, mit Schema, Host und ggf. Port. Fehlt eine, lehnt Argus Anfragen über diese Adresse ab.
:::

## Erster Administrator

| Variable | Standard | Bedeutung |
| --- | --- | --- |
| `ADMIN_USERNAME` | `admin` | Benutzername |
| `ADMIN_EMAIL` | – | E-Mail-Adresse |
| `ADMIN_PASSWORD` | – | Passwort, nur beim ersten Anlegen verwendet |

## Datenbank

| Variable | Standard | Bedeutung |
| --- | --- | --- |
| `POSTGRES_DB` | `argus` | Name der Datenbank |
| `POSTGRES_USER` | `argus` | Datenbankbenutzer |
| `POSTGRES_PASSWORD` | – | Pflicht. Passwort des Datenbankbenutzers |

## Backups

| Variable | Standard | Bedeutung |
| --- | --- | --- |
| `BACKUP_TIME` | `01:30` | Uhrzeit der täglichen Sicherung (in `TIME_ZONE`) |
| `BACKUP_KEEP_DAYS` | `14` | Aufbewahrungsdauer in Tagen |
| `BACKUP_DIR` | `/backups` | Ziel im Container (Volume `db-backups`). Leer schaltet die nächtliche Sicherung ab. |

Siehe [Backups](./backups).

## LDAP und Active Directory

Die LDAP-Anmeldung lässt sich vollständig in Argus einrichten (siehe [LDAP-Anmeldung](../administration/ldap)). Jede gesetzte Variable überschreibt den Wert aus Argus; er erscheint dort dann schreibgeschützt.

| Variable | Bedeutung |
| --- | --- |
| `LDAP_ENABLED` | `true` schaltet die LDAP-Anmeldung ein |
| `LDAP_SERVER_URI` | Server, kommagetrennt, z. B. `ldaps://dc1.firma.de,ldaps://dc2.firma.de` |
| `LDAP_START_TLS` | StartTLS auf einer `ldap://`-Verbindung |
| `LDAP_VERIFY_CERT` | Zertifikat des Servers prüfen |
| `LDAP_CA_CERT_FILE` | Pfad zu einer CA-Datei (PEM) im Container, für eine interne CA |
| `LDAP_TIMEOUT` | Zeitlimit in Sekunden |
| `LDAP_BIND_DN`, `LDAP_BIND_PASSWORD` | Dienstkonto für die Benutzersuche; leer = anonyme Suche |
| `LDAP_USER_SEARCH_BASE` | Suchbasis, z. B. `OU=Staff,DC=firma,DC=de` |
| `LDAP_USER_FILTER` | Suchfilter mit Platzhalter `{username}` |
| `LDAP_CREATE_USERS` | Benutzer bei der ersten Anmeldung anlegen |
| `LDAP_ATTR_USERNAME` | Attribut für den Benutzernamen (Standard `sAMAccountName`) |
| `LDAP_ATTR_FIRST_NAME` | Vorname (Standard `givenName`) |
| `LDAP_ATTR_LAST_NAME` | Nachname (Standard `sn`) |
| `LDAP_ATTR_EMPLOYEE_NUMBER` | Personalnummer (Standard `employeeID`) |
| `LDAP_ATTR_EMAIL` | E-Mail (Standard `mail`) |
| `LDAP_ATTR_JOB_TITLE` | Position (Standard `title`) |
| `LDAP_ATTR_PHONE` | Telefon (Standard `telephoneNumber`) |

Für eine interne CA binden Sie die PEM-Datei als Volume in den `app`-Container ein und setzen `LDAP_CA_CERT_FILE` auf ihren Pfad.
