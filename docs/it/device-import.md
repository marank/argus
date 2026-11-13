# Geräte importieren

**Geräte → Importieren** übernimmt Geräte aus einer Excel- oder CSV-Datei, z. B. einen Export aus dem MDM oder eine alte Inventarliste. Der Import legt neue Geräte an und aktualisiert vorhandene.

## 1. Datei

Unterstützt werden `.xlsx`, `.xlsm`, `.csv` und `.txt` mit bis zu 2000 Zeilen.

- **Excel:** Bei mehreren Tabellenblättern wählen Sie das richtige.
- **CSV:** Trennzeichen (Komma, Semikolon, Tab, senkrechter Strich) und Kodierung erkennt Argus selbst.
- **Ohne Spaltennamen:** Beginnt die Datei direkt mit Daten, schalten Sie **Erste Zeile enthält die Spaltennamen** aus. Argus erkennt das meist selbst. Die Spalten heißen dann „Spalte 1 · erster Wert“ usw.

Alte `.xls`-Dateien und kennwortgeschützte Dateien lassen sich nicht lesen. Speichern Sie sie in Excel als `.xlsx` ohne Kennwort oder als CSV.

## 2. Spalten zuordnen

Ordnen Sie jedem Gerätefeld die passende Spalte zu. Argus schlägt Zuordnungen anhand gängiger Spaltennamen vor, z. B. „Seriennummer“, „SN“, „Hostname“ oder „Asset Tag“.

Importierbar sind: Inventar-Nr., Seriennummer, Kennung, IMEI, MAC-Adresse, Gerätename, Modell, Status, Zustand, Standort, Mitarbeiter, Lieferant, Kaufdatum, Kaufpreis, Garantieende und Notizen.

### Neue Geräte

Hier legen Sie Werte für neue Geräte fest, die in der Datei fehlen: Modell, Standort, Status und Zustand. Vorhandene Geräte behalten ihre Werte.

Das **Modell** ist Pflicht, entweder als Spalte oder als Vorgabe für alle.

### Bereits erfasste Geräte

- **Erkennen an**: woran Argus ein vorhandenes Gerät erkennt, standardmäßig an der Seriennummer. Alternativ Inventar-Nr., IMEI, MAC-Adresse, Gerätename oder **Gar nicht**, dann ist jede Zeile ein neues Gerät.
- **Wenn gefunden**: vorhandene Geräte **mit den Werten der Datei aktualisieren** oder **unverändert lassen**.
- **Groß-/Kleinschreibung ignorieren**: beim Erkennen.

::: tip Tipp
Argus merkt sich die Zuordnung für Dateien mit denselben Spalten. Beim nächsten Export aus demselben System ist alles schon zugeordnet. Die Zuordnung gilt pro Browser.
:::

## 3. Vorschau

**Vorschau anzeigen** spielt den Import vollständig durch, ohne etwas zu speichern. Sie sehen für jede Zeile das Ergebnis:

| Ergebnis | Bedeutung |
| --- | --- |
| **Neu** | Gerät wird angelegt, mit der Inventarnummer, die es bekommen wird |
| **Aktualisieren** | Vorhandenes Gerät wird geändert, mit „alt → neu“ |
| **Unverändert** | Keine Änderung |
| **Übersprungen** | Vorhandenes Gerät, das unverändert bleiben soll |
| **Fehler** | Zeile wird nicht importiert, mit Grund |

Gibt es Fehler, zeigt die Vorschau zuerst diese Zeilen. Korrigieren Sie die Datei oder die Zuordnung und prüfen Sie erneut, oder importieren Sie nur die fehlerfreien Zeilen.

Mit **{n} Geräte importieren** übernehmen Sie das Ergebnis.

## Wie Argus Werte liest

- **Modell:** Name, Herstellerbezeichnung, Artikelnummer oder EAN, auch „Hersteller Name“ in einer Zelle, z. B. „Handtec HT60“.
- **Mitarbeiter:** Benutzername, E-Mail, „Nachname, Vorname“ oder „Vorname Nachname“.
- **Standort, Lieferant:** Name, bei Standorten auch das Kürzel.
- **Status, Zustand:** deutsche oder englische Bezeichnung, z. B. „Im Lager“.
- **Datum:** z. B. `2026-03-31`, `31.03.2026` oder `31.03.26`. Eine Uhrzeit dahinter wird ignoriert.
- **Preis:** `1.234,56` und `1,234.56`.
- **Leere Zellen** und Platzhalter wie `-` oder `--` überschreiben nie einen vorhandenen Wert.

::: info Gut zu wissen
- Jede Zeile durchläuft dieselben Prüfungen wie das Formular. Ein Mitarbeiter in der Datei setzt das Gerät auf **In Benutzung**; Gerätenamen vergibt Argus nach den Regeln der Kategorie.
- Nicht importierbar sind übergeordnetes Gerät, Pool-Kennzeichen, Verbrauchsmaterial und Komponenten.
- Findet Argus einen Wert mehrfach, z. B. dieselbe Seriennummer bei zwei Modellen, grenzt es über das Modell der Zeile ein. Bleibt es mehrdeutig, ist die Zeile ein Fehler.
:::
