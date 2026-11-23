# Prüfungen und Tests

`just check` (VS-Code-Task **Check: all**) führt dieselben Prüfungen aus wie die CI und muss
vor einem Push bestehen. Die Befehle stehen im `justfile`; die CI ruft dieselben Rezepte auf,
eines pro Job:

| Rezept | Prüft |
| --- | --- |
| `just check-backend` | ruff, mypy, kognitive Komplexität (complexipy), deptry, Schichten, Lizenzen, Migrationen, Django-Checks, Übersetzungen, OpenAPI-Schema, Tests |
| `just check-deploy` | `manage.py check --deploy` mit Produktionseinstellungen (`backend/deploy-check.env`) |
| `just check-frontend` | prettier, oxlint, ESLint, knip, Typen, Tests, kopierter Code (jscpd), API-Typen, Lizenzen, Build, Bundle-Größe |
| `just check-docs` | den Build der Dokumentation |
| `just check-workflows` | die GitHub-Workflows (actionlint, zizmor) |

`just check-eol` gehört nicht zu `just check`: Es fragt bei endoflife.date ab, wann Python,
Debian, Node.js, PostgreSQL und Django in den Versionen, die Argus verwendet, keine
Sicherheitsupdates mehr bekommen, und schlägt 180 Tage vorher fehl
(`backend/scripts/check_eol.py`). Die CI führt es im wöchentlichen Build aus.

`just fix` formatiert und behebt, was die Werkzeuge beheben können.

## Was sie sicherstellen

- **Lesbarkeit:** höchstens 15 kognitive Komplexität pro Funktion (complexipy, sonarjs) und
  höchstens 3 % kopierter Code (jscpd, `frontend/.jscpd.json`).
- **Coding-Agenten:** Claude Code formatiert und lintet jede Datei direkt nach der Bearbeitung
  (`.claude/settings.json`, `scripts/lint_file.py`).
- **Keine stummgeschalteten Prüfungen:** Jedes `# noqa`, `# type: ignore[…]` und
  `eslint-disable` nennt seine Regeln und eine Begründung; ungenutzte schlagen fehl.
- **Testreihenfolge:** pytest-randomly mischt die Backend-Tests bei jedem Lauf, sodass ein
  Test auffällt, der von einem anderen abhängt. `uv run pytest --randomly-seed=last`
  wiederholt die letzte Reihenfolge.
- **Coverage:** mindestens 90 % im Backend (`fail_under` in `pyproject.toml`); im Frontend
  eine Untergrenze auf dem heutigen Stand (`vitest.config.ts`, etwa 88 % der Zeilen;
  heben Sie sie an, wenn Tests hinzukommen).
- **Lizenzen:** Produktionsabhängigkeiten müssen mit der AGPL-3.0-or-later vereinbar sein.
  Permissive Lizenzen, LGPL, GPL-3.0 und AGPL-3.0 sind erlaubt, GPL-2.0-only, GPL ohne
  Version und SSPL nicht (`backend/scripts/check_licenses.py`,
  `frontend/scripts/check-licenses.mjs`; von Hand geprüfte Ausnahmen in `ALLOW`).
- **Ungenutzter Code:** `pnpm lint` enthält knip (ungenutzte Dateien, Exporte und
  Abhängigkeiten; `knip.jsonc`).
- **Bundle-Größe:** Das gebaute Bundle muss im Budget aus `package.json` bleiben
  (`size-limit`; heben Sie es bewusst an, wenn eine Funktion es erfordert).
- **Generierte Dateien:** Migrationen, `frontend/openapi.json` und
  `frontend/src/api/schema.d.ts` müssen zum Code passen.
- **Lesbarkeit:** Grenzen für Verschachtelung, nicht für Länge. Zyklomatische Komplexität
  höchstens 15 (ruff `C90`, ESLint `complexity`, wobei ein `switch` einmal zählt) und im
  Frontend Verschachtelungstiefe höchstens 4. Eine Funktion über der Grenze bekommt einen
  `noqa`- oder `eslint-disable`-Kommentar mit Begründung oder wird aufgeteilt.
- **Schichten:** In jeder Backend-App darf `api` `services` und `models` importieren,
  `services` darf `models` importieren, nie umgekehrt; die Modelle von `core` importieren
  keine andere App (import-linter, Verträge in `pyproject.toml`). Im Frontend nutzt nur
  `src/api/` den HTTP-Client, gemeinsame Komponenten und Composables importieren keine View,
  und `src/utils/` bleibt rein (ESLint `no-restricted-imports`).
- **Übersetzungen:** kein unübersetzter oder unscharfer (fuzzy) Eintrag in
  `backend/locale/de`, und `django.mo` passt zu `django.po`
  (`backend/scripts/check_translations.py`).

`check --deploy` läuft mit Produktionseinstellungen; HSTS und die HTTPS-Weiterleitung
bleiben dem TLS-Proxy überlassen und sind in `settings.py` stummgeschaltet. Die CI führt
zusätzlich Trivy aus: Secrets, behebbare kritische Schwachstellen und
Fehlkonfigurationen im Dockerfile lassen den Build fehlschlagen, sowohl im Repository als
auch im gebauten Image; Schwachstellen der Stufe HIGH werden gemeldet.

## Vor jedem Commit

Schnelle Prüfungen (ruff, prettier, oxlint, Leerzeichen) mit
[pre-commit](https://pre-commit.com), einmalig installiert:

```bash
uv tool run pre-commit install
```

## Backend-Tests

Die Backend-Tests laufen parallel (pytest-xdist, bis zu 8 Worker) mit
`config/settings_test.py`, sodass Variablen in der Umgebung sie nicht verändern. Für eine
einzelne Datei oder einen einzelnen Test überspringt `-n0` den Start der Worker:

```bash
just test-backend -n0 apps/accounts/tests/test_roles.py
```

::: info Gut zu wissen
Ohne die gettext-Werkzeuge (unter Windows üblich) prüft die Übersetzungsprüfung nur die
committete `.po`-Datei und warnt, dass neue Zeichenketten im Code nicht erfasst sind; die
CI hat sie. Unter Windows: `winget install mlocati.GetText`.
:::
