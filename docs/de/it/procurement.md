# Beschaffung

Die Beschaffung führt von fehlenden Geräten und Material zur Bestellung und vom Wareneingang zurück zur wartenden Anforderung.

## Bedarf

**Beschaffung → Bedarf** zeigt, was der Bestand nicht abdeckt. Markieren Sie Zeilen und fassen Sie sie mit **Bestellung anlegen** zu einer Bestellung zusammen.

### Aus Anforderungen

Offene Positionen von Anforderungen mit Status **Eingereicht** oder **Bestätigt**:

| Spalte | Bedeutung |
| --- | --- |
| **Nicht zugewiesen** | Was der Anforderung noch fehlt |
| **Im Pool** | Was im Lager verfügbar ist |
| **Bestellt** | Was für diese Position schon bestellt ist |
| **Zu bestellen** | Was dann noch fehlt |

Positionen, die der Bestand abdeckt, sind ausgeblendet. Sie lassen sich einblenden, aber nicht bestellen.

### Unter Mindestbestand

Verbrauchsmaterial, dessen Bestand unter dem Mindestbestand liegt, mit dem bereits bestellten Anteil.

::: info Gut zu wissen
- Anforderungen **In Genehmigung** erscheinen noch nicht, solche, die bereit zur Übergabe sind, und spätere nicht mehr.
- Jede Position wird für sich berechnet. Ein freies Gerät kann deshalb mehrere Anforderungen gleichzeitig als gedeckt erscheinen lassen.
- Bei „beliebiges Modell“ zählen nur Modelle der Kategorie selbst, nicht ihrer Unterkategorien.
- Sonderwünsche zählen erst gegen den Bestand, wenn ihnen ein Modell zugeordnet ist.
:::

## Bestellungen

**Beschaffung → Bestellungen** listet alle Bestellungen. Ist ein erwarteter Liefertermin überschritten, ist er hervorgehoben.

### Status

| Status | Bedeutung |
| --- | --- |
| **Zu bestellen** | Entwurf, Positionen noch änderbar |
| **Bestellt** | Beim Lieferanten bestellt |
| **Teilweise geliefert** | Ein Teil ist eingegangen |
| **Geliefert** | Alles ist eingegangen |
| **Storniert** | Abgebrochen |

### Bestellung anlegen und abschicken

1. Aus dem Bedarf oder über **Neue Bestellung**.
2. **Lieferant** wählen. Aus dem Bedarf ist der Standardlieferant des Modells vorbelegt.
3. Positionen prüfen: Modell oder Beschreibung, Menge, Einzelpreis. Ohne Preis gilt der Listenpreis des Modells.
4. **Als bestellt markieren** mit Bestelldatum, erwartetem Liefertermin und Referenz des Lieferanten.

Positionen lassen sich nur im Status **Zu bestellen** ändern. Lieferant, Referenz, Liefertermin, Lieferort und Notizen bleiben bis zur Lieferung änderbar.

### Stornieren und löschen

- **Bestellung stornieren** geht bei **Zu bestellen** und **Bestellt**, nicht mehr nach einer Teillieferung.
- **Löschen** geht nur bei **Zu bestellen**.

## Wareneingang

**Wareneingang** bucht eingegangene Ware. Wählen Sie unter **Lieferung an** den Lagerort; er gilt für alle Positionen.

| Art | Eingabe | Ergebnis |
| --- | --- | --- |
| **Einzelgeräte** | Seriennummern scannen, eine pro Zeile. Ohne Seriennummern nur die Menge. | Neue Geräte im Lager, mit Lieferant, Kaufdatum heute, Preis und Garantieende aus der Garantiedauer des Modells. Inventarnummer und Gerätename nach den Regeln der Kategorie. |
| **Verbrauchsmaterial** | Menge | Bestand am Lagerort steigt (Bewegung **Wareneingang**) |
| **Softwarelizenz** | Menge | Nur als geliefert gezählt. Die Lizenz legen Sie unter [Lizenzen](./licenses) an. |

Teillieferungen buchen Sie nacheinander. Die Bestellung steht dann auf **Teilweise geliefert**, bis alles da ist.

### Direkt an die wartende Anforderung

Gehört eine Position zu einer Anforderung mit Status **Bestätigt**, weist Argus die gelieferten Geräte und das Material direkt dieser Anforderung zu. Die Geräte sind dann **Reserviert**, und die Vorbereitung der Anforderung kann abgeschlossen werden.

Steht die Anforderung nicht mehr auf **Bestätigt**, geht die Ware ins Lager.

::: warning Achtung
- Der Wareneingang gilt ganz oder gar nicht. Bei einem Fehler, z. B. einer bereits vorhandenen Seriennummer, wird nichts gebucht.
- Positionen ohne Modell, also nur mit Beschreibung, lassen sich nicht einbuchen. Ordnen Sie Sonderwünschen deshalb vor dem Bestellen ein Modell zu.
:::

## Bestellnummern

Bestellnummern vergibt Argus aus der Nummernserie für Bestellungen, standardmäßig `PO-2026-0001` mit Neustart jedes Jahr. Siehe [Nummernserien](./administration/master-data#nummernserien).
