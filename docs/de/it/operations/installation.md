# Installation

Argus läuft als Docker-Compose-Projekt mit zwei Diensten:

| Dienst | Aufgabe |
| --- | --- |
| `app` | Argus selbst: Weboberfläche, API, Hintergrundjobs, Live-Updates und die nächtliche Sicherung (siehe [Backups](./backups)) in einem Container |
| `db` | PostgreSQL-Datenbank |

## Voraussetzungen

- Ein Linux-Server mit Docker Engine und dem Compose-Plugin
- Für den Echtbetrieb ein TLS-Proxy davor (z. B. nginx, Traefik oder Caddy), siehe [Hinter einem TLS-Proxy](#hinter-einem-tls-proxy)
- Optional ein SMTP-Server für E-Mails und ein LDAP- oder Active-Directory-Server für die Anmeldung

Es gibt zwei Wege:

| Weg | Wann |
| --- | --- |
| [Mit fertigem Image](#mit-fertigem-image) | Empfohlen. Der Server braucht nur zwei Dateien und Zugriff auf `ghcr.io`. |
| [Aus dem Repository bauen](#aus-dem-repository-bauen) | Für eigene Änderungen am Code. Das Image wird auf dem Server gebaut. |

## Mit fertigem Image

Die CI veröffentlicht Argus öffentlich als `ghcr.io/marank/argus:latest`, den aktuellen Stand von `main`. Dieses Image ist in `compose.yml` voreingestellt.

1. Ein Verzeichnis anlegen, z. B. `/opt/argus`, und `compose.yml` und `.env.example` aus dem Repository hineinlegen.

2. Konfiguration anlegen, siehe [Konfiguration anlegen](#konfiguration-anlegen).

3. Image holen und Argus mit Datenbank starten:

   ```bash
   docker compose pull app
   ```

   ```bash
   docker compose up -d
   ```

## Aus dem Repository bauen

1. Repository auf den Server holen:

   ```bash
   git clone https://github.com/marank/argus.git /opt/argus
   ```

2. Konfiguration anlegen, siehe [Konfiguration anlegen](#konfiguration-anlegen), und das selbst gebaute Image eintragen:

   ```ini
   ARGUS_IMAGE=argus:latest
   ```

3. Image bauen und starten:

   ```bash
   docker build -t argus:latest .
   ```

   ```bash
   docker compose up -d
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

Einen geeigneten Zufallswert für `SECRET_KEY` und `POSTGRES_PASSWORD` erzeugt:

```bash
openssl rand -hex 32
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
