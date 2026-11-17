# Einrichtung

Argus besteht aus einem Django-Backend (`backend/`, REST-API mit Django Ninja) und einer
Single-Page-App mit Vue 3 und TypeScript (`frontend/`, Naive UI) und wird als ein
Docker-Image ausgeliefert. Die Konventionen, denen jede Änderung folgt, stehen in
[AGENTS.md](https://github.com/marank/argus/blob/main/AGENTS.md); wie Sie eine Änderung
vorschlagen, steht in [CONTRIBUTING.md](https://github.com/marank/argus/blob/main/CONTRIBUTING.md).

| Teil          | Technik                                                            |
| ------------- | ------------------------------------------------------------------ |
| Backend       | Python 3.14 · Django 6.1 · Django Ninja · verwaltet mit `uv`       |
| Frontend      | Vue 3.5 · TypeScript · Vite · Naive UI · Pinia · vue-i18n · `pnpm` |
| Dokumentation | VitePress (diese Seite), `pnpm`                                    |

## Voraussetzungen

- [uv](https://docs.astral.sh/uv/) (installiert die passende Python-Version selbst)
- Node.js 22.18+ oder 24.12+ und [pnpm](https://pnpm.io/)
- Docker, nur für PostgreSQL und zum Bauen des Images

## Lokal starten

```bash
cd backend
uv sync
uv run python manage.py migrate
uv run python manage.py seed_demo      # optionale Demodaten
uv run python manage.py runserver
```

In einem zweiten Terminal:

```bash
cd frontend
pnpm install
pnpm dev                               # http://localhost:5173, leitet /api an :8000 weiter
```

Für die lokale Entwicklung ist keine `.env` nötig: Ohne `SECRET_KEY` läuft Django im
Debug-Modus mit einer SQLite-Datei (`backend/db.sqlite3`). Läuft das Backend unter einer
anderen Adresse, setzen Sie `BACKEND_URL`, z. B. `BACKEND_URL=http://127.0.0.1:8010 pnpm dev`.

### Mit PostgreSQL

Für die meisten Arbeiten genügt SQLite. Die Jobwarteschlange und die Live-Updates brauchen
PostgreSQL: Starten Sie eine Instanz mit `docker compose -f compose.dev.yml up -d` und das
Backend mit `DB_HOST=localhost`. Ohne PostgreSQL laufen Jobs (z. B. E-Mails) direkt nach
der Anfrage, und Seiten aktualisieren sich nicht von selbst.

## VS-Code-Tasks

*Terminal → Run Task…* bietet alles als Task an (`.vscode/tasks.json`), darunter:

| Task | Was er tut |
| --- | --- |
| **Dev: start all** | Django auf :8000 und Vite auf :5173 |
| **DB: start dev postgres** | PostgreSQL aus `compose.dev.yml` |
| **DB: seed demo data** | `seed_demo` |
| **DB: make migrations** | nach Änderungen an Modellen |
| **API: update types** | nach Änderungen an der API, siehe [API-Typen und Übersetzungen](./api-and-translations) |
| **Check: all** | alles, was die CI ausführt, siehe [Prüfungen und Tests](./checks) |
| **Docker: build and start** | baut das Image und startet es mit `compose.yml` |

## Demodaten

`seed_demo` füllt eine leere Datenbank. Alle Demokonten haben das Passwort `argus-demo`:

| Benutzer | Rolle |
| --- | --- |
| `admin` | Superuser |
| `it` | IT-Abteilung |
| `employee`, `sales` | Mitarbeitende |
| `terminal` | gemeinsames Abholterminal |

Außerdem legt es etwa 25 weitere Mitarbeitende an (z. B. `jkoch` in der IT), einen zweiten
Standort, rund 150 Geräte mit Verlauf, Anforderungen in jedem Schritt, Bestellungen,
Lizenzen und Problemmeldungen.

## Weiter

- [Architektur](./architecture): Aufbau, Konventionen und die Fachbegriffe
- [Prüfungen und Tests](./checks): was vor einem Push bestehen muss
- [API-Typen und Übersetzungen](./api-and-translations)
- [Dokumentation schreiben](./documentation)
- [CI und Releases](./ci)
