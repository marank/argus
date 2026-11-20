# API-Typen und Übersetzungen

## API-Typen

Die Typen des Frontends für API-Payloads werden aus dem OpenAPI-Schema des Backends
generiert. Führen Sie nach einer Änderung an einem Endpunkt oder Schema `just api-types`
aus (VS-Code-Task **API: update types**). Das exportiert `frontend/openapi.json` aus Django
und erzeugt daraus `frontend/src/api/schema.d.ts`.

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
just messages            # neue Zeichenketten in locale/de/LC_MESSAGES/django.po aufnehmen
# in django.po übersetzen
just compile-messages    # django.po -> django.mo
```

Committen Sie beide Dateien; `just check-backend` schlägt bei unübersetzten oder unscharfen
Einträgen fehl und wenn `django.mo` nicht zu `django.po` passt. Beide Rezepte brauchen die
gettext-Werkzeuge.
