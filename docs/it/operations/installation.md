# Installation

Argus läuft als Docker-Compose-Projekt mit drei Diensten:

| Dienst | Aufgabe |
| --- | --- |
| `app` | Argus selbst: Weboberfläche, API, Hintergrundjobs und Live-Updates in einem Container |
| `db` | PostgreSQL-Datenbank |
| `backup` | Sichert die Datenbank jede Nacht, siehe [Backups](./backups) |

## Voraussetzungen

- Ein Linux-Server mit Docker Engine und dem Compose-Plugin
- Für den Echtbetrieb ein TLS-Proxy davor (z. B. nginx, Traefik oder Caddy), siehe [Hinter einem TLS-Proxy](#hinter-einem-tls-proxy)
- Optional ein SMTP-Server für E-Mails und ein LDAP- oder Active-Directory-Server für die Anmeldung

Es gibt zwei Wege:

| Weg | Wann |
| --- | --- |
| [Mit fertigem Image](#mit-fertigem-image) | Der Server braucht nur zwei Dateien und Zugriff auf die Registry. Die nächtliche Sicherung richten Sie selbst ein. |
| [Aus dem Repository bauen](#aus-dem-repository-bauen) | Das Image wird auf dem Server gebaut. Enthält die nächtliche Sicherung. |

## Mit fertigem Image

Ersetzen Sie `registry.example.com/it/argus` durch die Adresse Ihrer Registry. Die CI veröffentlicht dort jede Version:

| Tag | Inhalt |
| --- | --- |
| `registry.example.com/it/argus:1` | Neueste Version 1.x. Empfohlen: erhält Updates, aber keine inkompatiblen Änderungen. |
| `registry.example.com/it/argus:1.2.3` | Genau diese Version |
| `registry.example.com/it/argus:latest` | Aktueller Stand von `main` |

Versions-Tags wie `:1` entstehen, sobald eine Version im Repository getaggt ist (z. B. `v1.0.0`). Bis dahin gibt es nur `:latest`.

1. Ein Verzeichnis anlegen, z. B. `/opt/argus`, und `compose.yml` und `.env.example` aus dem Repository hineinlegen.

2. Konfiguration anlegen, siehe [Konfiguration anlegen](#konfiguration-anlegen), und das Image eintragen:

   ```ini
   ARGUS_IMAGE=registry.example.com/it/argus:1
   ```

3. Bei der Registry anmelden, falls sie eine Anmeldung verlangt:

   ```bash
   docker login registry.example.com
   ```

4. Image holen und Argus mit Datenbank starten:

   ```bash
   docker compose pull app
   ```

   ```bash
   docker compose up -d --no-build app
   ```

::: warning Achtung
Der Dienst `backup` braucht ein Skript aus dem Repository und läuft auf diesem Weg nicht mit. Richten Sie die Sicherung der Datenbank selbst ein, siehe [Backups](./backups#ohne-backup-dienst).
:::

## Aus dem Repository bauen

1. Repository auf den Server holen (Adresse durch die Ihres Repositorys ersetzen):

   ```bash
   git clone https://git.example.com/it/argus.git /opt/argus
   ```

2. Konfiguration anlegen, siehe [Konfiguration anlegen](#konfiguration-anlegen). `ARGUS_IMAGE` bleibt leer.

3. Image bauen und starten:

   ```bash
   docker compose up --build -d
   ```

## Konfiguration anlegen

Für beide Wege gleich:

```bash
cp .env.example .env
```

In `.env` mindestens diese Werte setzen:

| Variable | Wert |
| --- | --- |
| `APP_URLS` | Die Adresse, unter der Argus erreichbar ist, z. B. `https://argus.firma.de` |
| `SECRET_KEY` | Zufallswert mit mindestens 40 Zeichen |
| `ADMIN_PASSWORD` | Passwort des ersten Administrators |
| `POSTGRES_PASSWORD` | Passwort der Datenbank |

Einen geeigneten `SECRET_KEY` erzeugt:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

Alle weiteren Variablen stehen unter [Konfiguration](./configuration).

## Nach dem Start

Argus ist unter `http://<server>:8080` erreichbar (Port über `APP_PORT` änderbar). Melden Sie sich mit `ADMIN_USERNAME` (Standard `admin`) und `ADMIN_PASSWORD` an.

Bei jedem Start wartet der Container auf die Datenbank, spielt ausstehende Migrationen ein und stellt sicher, dass der erste Administrator existiert.

::: info Gut zu wissen
- `ADMIN_PASSWORD` wird nur beim Anlegen des Benutzers verwendet. Spätere Änderungen in `.env` haben keine Wirkung. Ändern Sie das Passwort nach der ersten Anmeldung unter **Anmeldung & Sicherheit**.
- Der erste Administrator erhält bei jedem Start wieder Administratorrechte. Entziehen Sie ihm die Rechte in Argus, gilt das nur bis zum nächsten Neustart. Eine Deaktivierung bleibt dagegen bestehen.
- Ohne gültigen `SECRET_KEY` startet Argus nicht: Er fehlt, ist kürzer als 40 Zeichen oder ist ein Platzhalter wie `change-me`.
:::

## Testinstanz mit Demodaten

Mit `APP_DEMO_DATA=true` füllt Argus eine Datenbank ohne Geräte beim Start mit Beispieldaten: rund 150 Geräte mit Historie, Anforderungen in allen Schritten, Bestellungen, Lizenzen und Problemmeldungen. Alle Demo-Benutzer haben das Passwort `argus-demo`:

| Benutzer | Rolle |
| --- | --- |
| `admin` | Administrator |
| `it` | IT-Abteilung |
| `employee`, `sales` | Mitarbeitende |
| `terminal` | Abholterminal |

Sind bereits Geräte erfasst, legt Argus keine Demodaten an.

::: danger Wichtig
Demodaten nie auf einer produktiven Instanz aktivieren: Die Demo-Benutzer haben ein bekanntes Passwort.
:::

## Hinter einem TLS-Proxy

Der Container spricht nur HTTP auf Port 8080. Für den Echtbetrieb gehört ein TLS-Proxy davor.

1. Der Proxy leitet an `http://<server>:8080` weiter und setzt die Header `X-Forwarded-For` und `X-Forwarded-Proto`.
2. `APP_URLS` enthält die `https://`-Adresse.
3. `TRUSTED_PROXIES` enthält die IP-Adresse (oder den CIDR-Bereich) des Proxys.

```ini
APP_URLS=https://argus.firma.de
TRUSTED_PROXIES=10.0.0.5
```

Nur Anfragen von den Adressen in `TRUSTED_PROXIES` dürfen Client-Adresse und HTTPS weitergeben. Fehlt der Eintrag, ignoriert Argus diese Header. Dann schlagen Anmeldungen über HTTPS fehl. Außerdem teilen sich alle Benutzer die Adresse des Proxys, sodass die Sperre nach Fehlversuchen (30 pro Adresse in 15 Minuten) alle gleichzeitig trifft. Der Container warnt beim Start, wenn `APP_URLS` HTTPS-Adressen enthält, `TRUSTED_PROXIES` aber leer ist.

### Live-Updates durch den Proxy

Argus hält pro geöffnetem Tab eine Verbindung zu `/api/events` offen, über die Änderungen sofort ankommen. Der Proxy darf diese Verbindung nicht puffern:

- **nginx:** für `/api/events` `proxy_buffering off;` setzen
- **Traefik, Caddy:** reichen den Datenstrom in der Regel ohne Anpassung durch

Spricht der Proxy HTTP/2 mit dem Browser, gibt es keine Begrenzung bei vielen Tabs. Wird Argus direkt über `http://…:8080` aufgerufen, erlauben Browser nur sechs gleichzeitige Verbindungen pro Adresse. Ab etwa sechs offenen Argus-Tabs hängen dann weitere Anfragen, bis ein Tab geschlossen wird.

HSTS setzt Argus nicht selbst; das ist Aufgabe des Proxys.

## Nächste Schritte

- [Konfiguration](./configuration): alle Umgebungsvariablen
- [Erste Schritte für Administratoren](../administration/getting-started): von der leeren Instanz zum Echtbetrieb
- [Backups](./backups): Sicherung prüfen und außer Haus kopieren
