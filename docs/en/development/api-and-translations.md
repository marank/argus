# API types and translations

## API types

The frontend's types for API payloads are generated from the backend's OpenAPI schema.
After changing an endpoint or a schema, run the VS Code task **API: update types**, or:

```bash
cd backend && uv run python manage.py export_openapi ../frontend/openapi.json
```

```bash
cd frontend && pnpm api:types
```

Commit `frontend/openapi.json` and `frontend/src/api/schema.d.ts`; CI fails when they do
not match the code. `src/types/` refers to them (`Schemas['AssetOut']`), so a changed API
shows up as a type error in the frontend.

## Translations

The interface is written in English and translated to German.

**Frontend:** every visible text goes through vue-i18n, one file per area in
`frontend/src/i18n/locales/en/` and `de/`.

**Backend** (mails, error messages, the Django admin): strings are wrapped in `gettext`
and translated in `backend/locale/de`:

```bash
cd backend
uv run python manage.py makemessages -l de --ignore ".venv/*"
# edit locale/de/LC_MESSAGES/django.po
uv run python manage.py compilemessages
```
