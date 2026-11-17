# API-Typen und Übersetzungen

## API-Typen

Die Typen des Frontends für API-Payloads werden aus dem OpenAPI-Schema des Backends
generiert. Führen Sie nach einer Änderung an einem Endpunkt oder Schema den VS-Code-Task
**API: update types** aus, oder:

```bash
cd backend && uv run python manage.py export_openapi ../frontend/openapi.json
```

```bash
cd frontend && pnpm api:types
```

Committen Sie `frontend/openapi.json` und `frontend/src/api/schema.d.ts`; die CI schlägt
fehl, wenn sie nicht zum Code passen. `src/types/` verweist auf sie (`Schemas['AssetOut']`),
sodass eine geänderte API im Frontend als Typfehler sichtbar wird.

## Übersetzungen

Die Oberfläche ist auf Englisch geschrieben und ins Deutsche übersetzt.

**Frontend:** Jeder sichtbare Text läuft über vue-i18n, eine Datei pro Bereich in
`frontend/src/i18n/locales/en/` und `de/`.

**Backend** (E-Mails, Fehlermeldungen, der Django-Admin): Zeichenketten werden in
`gettext` eingeschlossen und in `backend/locale/de` übersetzt:

```bash
cd backend
uv run python manage.py makemessages -l de --ignore ".venv/*"
# locale/de/LC_MESSAGES/django.po bearbeiten
uv run python manage.py compilemessages
```
