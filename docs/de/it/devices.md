# Geräte

Unter **IT-Betrieb → Geräte** stehen alle einzeln geführten Geräte: Notebooks, Smartphones, Headsets, MDE und alles andere mit eigener Inventarnummer.

## Die Liste

Die Liste ist standardmäßig nach Kategorie gruppiert. Über die Kopfzeile ändern Sie Gruppierung, Spalten und Zeilenhöhe; **Ansicht zurücksetzen** stellt den Ausgangszustand wieder her.

- **Suche** über Inventarnummer, Seriennummer, Kennung, IMEI, MAC-Adresse, Gerätename, Modell, Hersteller, Mitarbeiter und die Seriennummern eingebauter Teile.
- **Filter** für Status, Kategorie (inklusive Unterkategorien), Modell, Standort, Mitarbeiter, Hersteller, Lieferant, Pool, Kaufdatum und Garantieende. Zeiträume geben Sie z. B. als `0611..2311` ein.
- **Zugewiesen an** zeigt bei reservierten Geräten „reserviert für {Name}“.

Links aus Dashboard, Kalender und Modellen öffnen die Liste bereits gefiltert.

## Gerät anlegen

Es gibt vier Wege:

| Weg | Wann |
| --- | --- |
| **Neues Gerät** | Ein einzelnes Gerät mit allen Angaben |
| **Mehrere einscannen** | Viele Geräte eines Modells: Seriennummern nacheinander scannen, bis zu 500 auf einmal |
| **Serie anlegen** | Viele gleiche Geräte ohne Seriennummer, z. B. vor der Auslieferung; Seriennummern folgen später |
| **Importieren** | Bestand aus einer Excel- oder CSV-Datei, siehe [Geräte importieren](./device-import) |

Außerdem legt der [Wareneingang](./procurement#wareneingang) einer Bestellung Geräte automatisch an.

### Felder

**Identifikation**

- **Modell**: Pflicht. Nur aktive Modelle, die als Einzelgeräte geführt werden.
- **Inventar-Nr.**: leer lassen, dann vergibt Argus die nächste Nummer aus der Nummernserie des Modells oder seiner Kategorie. Muss eindeutig sein.
- **Gerätename**: siehe [Gerätenamen](#geratenamen).
- **Seriennummer**: eindeutig je Modell.
- **Kennung**: eine weitere Herstellernummer, z. B. die Ausführung (Handtec CN, Lenovo MTM). Die Kategorie legt fest, wie das Feld heißt.
- **IMEI**, **MAC-Adresse**: Die MAC-Adresse wird in jeder Schreibweise akzeptiert und als `AA:BB:CC:DD:EE:FF` gespeichert.
- **Gehört zu**: ein übergeordnetes Gerät, z. B. die Dockingstation zum Notebook.

**Komponenten**: Hat die Kategorie austauschbare Teile wie Akkus, erfassen Sie hier deren Seriennummer und Einbaudatum.

**Status & Nutzung**: Status, Zustand (Neu, Gut, Gebraucht, Defekt), Standort, Mitarbeiter, zugeordnetes Verbrauchsmaterial und **Verleihbar (Pool)**.

**Kauf & Garantie**: Lieferant, Kaufpreis, Kaufdatum, Garantieende, Notizen.

::: info Gut zu wissen
**Verleihbar (Pool)** ist standardmäßig an. Nur Geräte im Pool stehen für Anforderungen zur Verfügung und werden automatisch zugewiesen. Schalten Sie es für Geräte aus, die nicht verliehen werden sollen, z. B. Server.
:::

## Status

| Status | Bedeutung | Wie er entsteht |
| --- | --- | --- |
| **Im Lager** | Verfügbar | beim Anlegen, nach Rücknahme |
| **Reserviert** | Für eine Anforderung zugewiesen | automatisch beim Zuweisen |
| **In Benutzung** | Bei einem Mitarbeiter | automatisch bei Ausgabe oder Zuweisung |
| **In Reparatur** | Defekt oder beim Service | von Hand, bei Rücknahme als defekt, beim Ersetzen |
| **Verloren** | Nicht auffindbar | nur von Hand |
| **Ausgemustert** | Außer Betrieb | von Hand oder beim Ersetzen |

Jeder Statuswechsel steht im Servicebuch des Geräts.

::: warning Achtung
- Ein reserviertes Gerät lässt sich nicht ändern, solange es einer Anforderung zugewiesen ist. Entfernen Sie es zuerst dort.
- Eine Meldung „Verloren oder gestohlen“ ändert den Status nicht. Setzen Sie ihn selbst auf **Verloren**.
- Beim Ausmustern oder bei „Verloren“ bleiben Mitarbeiter und Lizenzen am Gerät. Entfernen Sie sie bei Bedarf von Hand.
:::

## Die Geräteseite

Die Geräteseite zeigt alle Angaben, das Modell mit Support-Kontakten, zugeordnetes Verbrauchsmaterial, Lizenzen und die **Historie**. Ist das Gerät einer Anforderung zugewiesen oder über eine ausgegeben, steht oben ein Hinweis mit Link. Offene Meldungen erscheinen ebenfalls oben.

Aktionen:

| Aktion | Wofür |
| --- | --- |
| **Zurücknehmen** | Gerät vom Mitarbeiter zurücknehmen. Lief es über eine Anforderung, gilt es dort als zurückgegeben. |
| **Anforderung erstellen** | Anforderung für dieses Modell anlegen (nur im Lager) |
| **Schnellzuweisung** | Gerät sofort einem Mitarbeiter geben (nur im Lager) |
| **Ersetzen** | Gerät durch ein anderes aus dem Lager ersetzen |
| **Service erfassen** | Reparatur, Wartung, Prüfung oder Notiz eintragen |
| **Bearbeiten**, **Löschen** | Angaben ändern, Gerät löschen |

## Schnellzuweisung

Für den Fall „Gerät aus dem Regal, direkt an den Mitarbeiter“: **Schnellzuweisung** auf einem Gerät im Lager.

- **Mitarbeiter** wählen.
- **Befristet** mit **Rückgabe bis** oder **Dauerhaft**.
- **Zugewiesen ab**: leer für heute; ein früheres Datum erfasst eine Ausgabe, die schon stattgefunden hat.

Argus legt dabei eine Anforderung an, die sofort ausgegeben ist. Befristete Zuweisungen laufen wie jede Ausleihe: mit Erinnerungen, Überfälligkeit und Rücknahme. Der Mitarbeiter erhält die Benachrichtigung **Ausgegeben**.

Ohne Schreibrecht auf Anforderungen weist die Schnellzuweisung das Gerät nur zu, ohne Anforderung.

## Gerätenamen

Die **Inventarnummer** gehört für immer zum Gerät. Der **Gerätename** gehört zum Einsatzort, z. B. der Hostname eines PCs oder der Name eines MDE im MDM.

- Unter Geräten im Einsatz ist jeder Name nur einmal vergeben. Verlorene und ausgemusterte Geräte behalten ihren Namen für die Akte, blockieren ihn aber nicht.
- Die Kategorie legt fest, ob neue Geräte automatisch einen Namen bekommen: **Kein Name**, **Aus einer Nummernserie** (z. B. `pc-{seq}`) oder **Wie die Inventarnummer**.
- Automatisch vergeben wird nur beim Anlegen und nur, wenn das Feld leer bleibt.

## Gerät ersetzen

**Ersetzen** tauscht ein Gerät gegen eines aus dem Lager, z. B. bei einem Defekt:

1. **Ersatzgerät** wählen. Angeboten werden Geräte im Lager aus derselben Kategorie; mit **Auch aus anderen Kategorien** alle.
2. Unter **Danach ist dieses Gerät** festlegen, was mit dem alten Gerät passiert: **Im Lager**, **In Reparatur** (Standard) oder **Ausgemustert**.
3. **Gerät ersetzen**.

Das Ersatzgerät übernimmt Gerätenamen, Mitarbeiter und Standort. Beide Geräte erhalten im Servicebuch einen Eintrag mit Verweis aufeinander. Danach öffnet Argus das Ersatzgerät.

## Servicebuch

Jedes Gerät hat eine **Historie**. **IT-Betrieb → Servicebuch** zeigt alle Einträge über alle Geräte, mit Filtern nach Art, Modell und Zeitraum.

Automatisch erfasst Argus: **Angelegt**, **Status geändert**, **Ausgegeben**, **Zurückgegeben**, **Gerät ersetzt**, **Problem gemeldet** und **Problem behoben**.

Von Hand erfassen Sie mit **Service erfassen**:

| Art | Beispiel |
| --- | --- |
| **Komponente getauscht** | Akkutausch |
| **Reparatur** | Display ersetzt |
| **Wartung** | Reinigung, Firmware-Update |
| **Prüfung** | Elektroprüfung |
| **Notiz** | alles andere |

Zu jedem Eintrag gehören Datum, Kosten und Beschreibung. Bei **Komponente getauscht** und **Reparatur** geben Sie zusätzlich das Teil und seine neue Seriennummer an. Bei einem erfassten Teil wie dem Akku übernimmt das Gerät die neue Seriennummer; die alte bleibt im Eintrag erhalten.

Mit **Verbrauchsmaterial entnehmen** buchen Sie verwendetes Material gleich mit aus, z. B. einen Ersatzakku aus dem Lager.

Von Hand erfasste Einträge lassen sich löschen, automatische nicht.

## Gerät löschen

Ein Gerät lässt sich nur löschen, wenn es nie in einer Anforderung oder Bestellung vorkam. Sonst setzen Sie es auf **Ausgemustert**. Beim Löschen verschwinden auch Historie, Meldungen und Lizenzzuweisungen des Geräts.

::: tip Tipp
Ausmustern statt löschen: So bleibt nachvollziehbar, wer das Gerät wann hatte.
:::
