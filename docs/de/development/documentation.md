# Dokumentation schreiben

Diese Dokumentation liegt in `docs/` (VitePress). Das Image liefert sie unter `/docs/`
aus; das Benutzermenü der App verlinkt sie als *Hilfe*, in der Sprache der Oberfläche
(IT-Mitarbeitende nach `/docs/<lang>/it/`, alle anderen nach `/docs/<lang>/employees/`).

## Sprachen und Bereiche

Jede Seite gibt es auf Deutsch und Englisch, unter demselben Pfad in `de/` und `en/`. Der
Umschalter in der oberen Leiste führt zur selben Seite in der anderen Sprache. Eine
Änderung kommt im selben Commit in beide Fassungen; der Build schlägt fehl, wenn einer
Seite ihr Gegenstück fehlt.

Jede Sprache hat vier Bereiche mit eigener Navigation und Suche (VitePress-Locales in
`docs/.vitepress/config.mts`):

| Ordner | Für |
| --- | --- |
| `employees/`, `approvers/` | alle; dürfen öffentlich verlinkt werden |
| `it/` | tägliche IT-Arbeit, Administration und Betrieb |
| `development/` | Mitwirkende |

Seiten in `employees/` und `approvers/` verlinken nie nach `it/`; sonst schlägt der Build
fehl. Datei- und Ordnernamen sind englisch. Eine neue Seite kommt mit deutschem und
englischem Titel in `SIDEBARS` in der Konfiguration.

Verwenden Sie die genauen Bezeichnungen der Oberfläche aus
`frontend/src/i18n/locales/de` bzw. `.../en`. Alte Links ohne Sprachordner (`/docs/it/…`)
leitet nginx auf die deutschen Seiten um.

## Starten und bauen

```bash
cd docs
pnpm install
pnpm dev --port 5175      # http://localhost:5175/docs/; der Frontend-Dev-Server leitet /docs dorthin weiter
```

```bash
pnpm build                # schlägt auch bei toten Links, fehlenden Ankern, IT-Links in den offenen Bereichen und fehlenden Übersetzungen fehl
```

VS-Code-Tasks: **Dev: docs**, **Check: docs**.

Aktualisieren Sie die Benutzerdokumentation, sobald Benutzer oder Betreiber eine Änderung
bemerken.
