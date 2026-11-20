# API types and translations

## API types

The frontend's types for API payloads are generated from the backend's OpenAPI schema.
After changing an endpoint or a schema, run `just api-types` (VS Code task
**API: update types**). It exports `frontend/openapi.json` from Django and generates
`frontend/src/api/schema.d.ts` from it.

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
just messages            # adds new strings to locale/de/LC_MESSAGES/django.po
# translate them in django.po
just compile-messages    # django.po -> django.mo
```

Commit both files; `just check-backend` fails on untranslated or fuzzy entries and on a
`django.mo` that does not match `django.po`. Both recipes need the gettext tools.
