# Architektur

Die Regeln hinter diesem Aufbau (eine Datei pro Modell, Services, strikte Typisierung,
i18n) stehen in [AGENTS.md](https://github.com/marank/argus/blob/main/AGENTS.md).

## Aufbau

```
backend/
  config/            Einstellungen, URLs, Zusammenbau der API (config/api.py)
  apps/
    core/            Basismodelle, Nummernkreise, Anmelde-/Sitzungs-API, CRUD-Hilfen
    accounts/        Benutzer, Abteilungen, Teams, LDAP und Zwei-Faktor-Anmeldung
    masterdata/      Hersteller, Lieferanten, Kategorien, Modelle, Standorte
    inventory/       Geräte, Geräteereignisse, Verbrauchsmaterial und dessen Bewegungen
    requests/        Anforderungen, Positionen, Zuteilungen, Ablauf, Mitarbeiterportal
    procurement/     Bestellungen, Bedarfsberechnung, Wareneingang
    dashboard/       Kennzahlen der Übersicht
  Jede App: models/, schemas/, api/, services/, admin/ – eine Datei pro Konzept.
  locale/            deutsche Übersetzungen

frontend/src/
  api/               typisierte API-Clients pro Fachbereich
  types/             TypeScript-Typen pro Fachbereich (Aliasse des generierten Schemas)
  components/        layout, common, crud, inventory, requests, procurement
  views/             Seiten pro Bereich (portal, inventory, requests, …)
  composables/       Listenzustand, Aktionen, Formatierung, Scanner, Bestätigung
  i18n/locales/      en/ und de/, eine Datei pro Bereich
  theme/             Farbpalette und Naive-UI-Anpassungen (hell/dunkel)

docs/                diese Dokumentation (VitePress), ausgeliefert unter /docs/
docker/              nginx, supervisord, gunicorn und der Entrypoint des Images
```

## Konventionen

- **UUID-Schlüssel.** Alle Modelle verwenden UUIDs als Primärschlüssel
  (`apps.core.models.UUIDModel`, auch bei `accounts.User`); URLs und API-Payloads tragen
  diese UUIDs. Neue sind UUIDv7 (zufällig, in Erstellungsreihenfolge). `manage.py check`
  schlägt fehl (`core.E001`), wenn ein eigenes Modell keinen UUID-Primärschlüssel hat.
- **Services.** Geschäftsregeln liegen in `services/` (z. B.
  `apps/requests/services/workflow.py`); API-Module bleiben schlank.
- **Code und Daten auf Englisch**, Deutsch wird als Übersetzung ausgeliefert (Backend
  `locale/`, Frontend `src/i18n/locales/de`).

## Laufzeit

Ein Image enthält nginx (liefert das gebaute Frontend und diese Dokumentation aus, leitet
`/api` und `/admin` weiter), gunicorn (Django), uvicorn für den Live-Update-Stream
(`/api/events`) und den Procrastinate-Job-Worker, alle unter supervisord. docker compose
ergänzt PostgreSQL.

- **Jobs:** E-Mails, Erinnerungen und die nächtliche Sicherung laufen über eine
  Procrastinate-Warteschlange in PostgreSQL. Mit SQLite gibt es keine Warteschlange; Jobs
  laufen im selben Prozess direkt nach dem Commit der Transaktion.
- **Live-Updates:** Der Server meldet, was sich geändert hat (PostgreSQL LISTEN/NOTIFY,
  an den Browser als Server-Sent Events); Seiten laden ihre Daten dann über die normale
  API neu.

## Fachbegriffe

Links die Namen im Code, rechts die Begriffe der Oberfläche. URLs, API-Pfade,
Berechtigungsbereiche und Live-Themen heißen `request(s)`. „Reservierung“ wird nicht
verwendet: Eine Anforderung umfasst auch dauerhafte Ausgaben, Software und
Verbrauchsmaterial. „Reserviert“ bleibt als Gerätestatus erhalten (für eine Anforderung
zurückgelegt).

| Code                     | Oberfläche (de)         | Oberfläche (en)     |
| ------------------------ | ----------------------- | ------------------- |
| `AssetRequest`           | Anforderung             | Request             |
| `AssetRequestItem`       | Position                | Line                |
| `AssetRequestAllocation` | Zuteilung               | Allocation          |
| `Handover`               | Übergabe / Ausgabe      | Handover / hand-out |
| `DeviceReturn`           | Rückgabe                | Return              |
| `approve` (Abteilung)    | Genehmigung             | Approval            |
| `confirm` (IT)           | Bestätigung             | Confirmation        |
| `origin="direct"`        | Direktausgabe           | Direct hand-out     |
| `Asset.name`             | Gerätename              | Device name         |

Das Modell heißt `AssetRequest` (Variablen `asset_request`), nicht `Request`, um eine
Verwechslung mit dem Argument `request` jeder API-View zu vermeiden.
