# Dashboard und Kalender

## Dashboard

Das Dashboard der IT zeigt den aktuellen Stand von Inventar, Anforderungen und Beschaffung. Jeder sieht nur Widgets zu Bereichen, für die er Rechte hat und deren Modul eingeschaltet ist.

### Standard-Widgets

| Widget | Inhalt |
| --- | --- |
| **Meine Arbeit** | Offene Anforderungen nach Zuständigkeit: mir zugewiesen, meine Teams, nicht zugewiesen; dazu meine Meldungen |
| **Anforderungen** | Zu bestätigen, vorzubereiten, abholbereit, überfällige Rückgaben |
| **Beschaffung & Bestand** | Zu bestellen, bestellt und unterwegs, unter Mindestbestand |
| **Fristen & Meldungen** | Offene Meldungen, ablaufende Lizenzen und Garantien |
| **Geräte nach Status** | Verteilung aller Geräte |
| **Anstehende Ausgaben** | Was in den nächsten Tagen ausgegeben werden soll, Überfälliges markiert |
| **Letzte Aktivitäten** | Die letzten zehn Arbeitsschritte aus allen Bereichen, die Sie lesen dürfen; eine Ausgabe mehrerer Geräte ist eine Zeile. **Alle anzeigen** öffnet die [Aktivitäten](./activities) |

Jede Zahl führt per Klick zur passenden, gefilterten Liste.

### Weitere Widgets

Über **Dashboard anpassen → Widget hinzufügen**:

- **Meine Aufgaben**: Anforderungen und Meldungen, die Ihnen persönlich zugewiesen sind
- **Überfällige Rückgaben**: mit Button **Erinnern**
- **Diese Woche**: Kalendereinträge der nächsten 7 Tage
- **Team-Auslastung**: offene Anforderungen und Meldungen pro Person
- **Anforderungen pro Woche**: neue und abgeschlossene Anforderungen der letzten 12 Wochen
- **Bald fällige Rückgaben**, **Wartende Anforderungen**, **Ablaufende Lizenzen & Garantien**, **Verbrauchsmaterial knapp**, **Offene Bestellungen**
- **Schnellzugriff**: Buttons zu Seiten Ihrer Wahl
- **Notizen**: ein persönlicher Notizzettel, nur für Sie sichtbar

### Anpassen

**Dashboard anpassen** öffnet den Bearbeitungsmodus:

- Widgets per Drag & Drop verschieben
- **Breite** (Drittel, Halb, Voll) und **Höhe** wählen
- einzelne Kennzahlen mit dem Auge-Symbol ausblenden
- einen **eigenen Titel** vergeben

Manche Widgets lassen sich mehrfach hinzufügen, jeweils mit eigenen Einstellungen. **Standard wiederherstellen** setzt das Dashboard zurück. Das Layout wird pro Benutzer gespeichert.

Die Vorwarnzeiten für Lizenzen und Garantien legen Administratoren in den [Einstellungen](./administration/settings#fristen-vorwarnzeiten) fest.

## Kalender

**IT-Betrieb → Kalender** zeigt alle Termine der IT. Ansichten: **Monat**, **Woche** und **Liste**.

| Eintrag | Inhalt |
| --- | --- |
| **Anforderung** | Befristete Ausleihen als Balken vom Start- bis zum Enddatum |
| **Abholung** | Vereinbarter Abholtermin, sonst Wunschtermin oder Startdatum |
| **Rückgabe** | Fällige Rückgaben. Überfällige wandern täglich mit, bis sie erledigt sind. |
| **Lieferung** | Erwartete Liefertermine offener Bestellungen |
| **Garantie endet** | Ein Sammeleintrag pro Tag für alle Geräte, deren Garantie endet |
| **Lizenz endet** | Enddatum befristeter Lizenzen |

- **Ausgefüllt** = bestätigt, **nur Umriss** = noch nicht bestätigt, **rot** = überfällig.
- Dauerhafte Ausgaben erscheinen nicht als Balken, ihr Abholtag aber schon.
- Über die Reiter oben beschränken Sie Anforderungen auf **Mir zugewiesen**, **Meine Teams** oder **Nicht zugewiesen**.
- Über die Filter blenden Sie Eintragsarten aus. Argus merkt sich die Auswahl im Browser.

Garantie-, Lizenz- und Liefertermine lassen sich in den [Einstellungen](./administration/settings) einzeln abschalten.

::: info Gut zu wissen
Der Kalender aktualisiert sich nicht von selbst. Laden Sie ihn neu, um Änderungen anderer zu sehen.
:::
