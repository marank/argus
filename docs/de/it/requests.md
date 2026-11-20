# Anforderungen bearbeiten

Unter **IT-Betrieb → Anforderungen** bearbeitet die IT alle Anforderungen: bestätigen, Geräte zuweisen, Übergabe planen, ausgeben und zurücknehmen.

## Ablauf im Überblick

| Status | Was die IT tut |
| --- | --- |
| **In Genehmigung** | Nichts. Die Abteilung entscheidet zuerst. |
| **Eingereicht** | Prüfen, dann **Bestätigen** oder **Ablehnen**. |
| **Bestätigt** | Geräte zuweisen, fehlende bestellen, dann **Abholbereit melden**. |
| **Abholbereit** | Geräte am Terminal abholen lassen oder **Ausgeben**. |
| **Ausgegeben** | Bei Rückgabe **Zurücknehmen**, bei Bedarf **Leihfrist verlängern**. |
| **Abgeschlossen** | Nichts mehr. Dauerhafte Ausgaben lassen sich trotzdem zurücknehmen. |

Auf jeder Anforderung steht unter **Nächster Schritt**, was als Nächstes zu tun ist. Seltene Aktionen finden Sie unter **Weitere Aktionen** (⋮).

## Die Liste

Die Liste zeigt standardmäßig **Nur offene** Anforderungen. Weitere Ansichten: **Überfällig** und **Alle**. Filter gibt es für Status, Dauer, Abteilung, Team, Bearbeiter und Startdatum.

Die Spalte **Abholung** zeigt den vereinbarten Termin. Steht dort **Wunsch**, gibt es nur den Wunschtermin des Mitarbeiters; **verstrichen** bedeutet, dass der Termin vorbei ist.

## Zuständigkeit

Jede Anforderung hat ein **Team** und optional einen **Bearbeiter**. Neue Anforderungen gehen automatisch an das Team des ersten Modells oder seiner Kategorie, sonst an das Standard-Team. Benachrichtigungen über neue Anforderungen erhält dieses Team; ohne Team die ganze IT.

Team und Bearbeiter ändern Sie in der Karte **Zuständig** und übernehmen beides mit **Speichern**. Mit **Mir zuweisen** übernehmen Sie eine Anforderung sofort, ohne zu speichern. Weisen Sie sie jemand anderem zu, erhält diese Person eine Benachrichtigung. Mitarbeitende sehen die Zuständigkeit nicht.

## Bestätigen

**Bestätigen** öffnet einen Dialog mit der Verfügbarkeit jeder Position im angeforderten Zeitraum.

- Deckt der Bestand eine Position nicht, reduzieren Sie die Menge. Mit Menge 0 streichen Sie eine Position.
- Unter **Kommentar der IT** hinterlassen Sie dem Mitarbeiter eine Nachricht.

Der Mitarbeiter erhält eine Benachrichtigung. Wann und wo er die Geräte bekommt, legen Sie später beim Abholbereit-Melden fest.

Solange die Anforderung **Bestätigt** ist, ändern Sie die Mengen über **Bearbeiten**. Unter die Zahl bereits zugewiesener Geräte lässt sich eine Menge nicht senken. Der Mitarbeiter wird dabei nicht erneut benachrichtigt.

## Ablehnen und stornieren

- **Ablehnen** (bei Eingereicht oder Bestätigt) verlangt eine Begründung für den Mitarbeiter.
- **Anforderung stornieren** (unter ⋮) ist möglich, bis die Geräte ausgegeben sind. Zugewiesene Geräte gehen zurück in den Pool.

Der Mitarbeiter wird in beiden Fällen benachrichtigt.

## Ersetzen

Braucht der Mitarbeiter nachträglich etwas anderes oder zusätzlich, ersetzen Sie die Anforderung, solange sie nicht ausgegeben ist: **Ersetzen** (unter ⋮) öffnet den Warenkorb mit den Angaben und Positionen der Anforderung, bei einer Direktausgabe mit ihren Geräten. Ändern Sie, was nötig ist, und senden Sie ab.

- Die alte Anforderung wird storniert, im Verlauf steht **Ersetzt** mit der Nummer der neuen. Der Mitarbeiter erhält keine Mail.
- Die neue Anforderung zeigt **Folgt auf** mit der alten Nummer und übernimmt Zuständigkeit und geplante Übergabe.
- War die alte Anforderung bestätigt, ist es die neue auch. Zugewiesene Geräte wandern auf die passende neue Position; was nicht mehr passt, geht zurück in den Pool.
- Die Genehmigung gilt weiter: Wartete die alte Anforderung auf die Abteilung, wartet die neue ebenfalls, und die Genehmigenden werden benachrichtigt. War sie schon genehmigt, bleibt die neue genehmigt. Eine wartende Anforderung kann nicht als Direktausgabe ersetzt werden.
- Bei einer Direktausgabe nennt der Warenkorb, was er nicht übernehmen kann (noch fehlende Geräte einer Position, Lizenzplätze); wählen Sie es bei Bedarf neu aus.
- Die IT erhält keine Benachrichtigung über eine neue Anforderung.

::: info Gut zu wissen
Erst beim Absenden wird storniert. Brechen Sie im Warenkorb ab, bleibt die Anforderung unverändert.
:::

## Sonderwünsche

Positionen, die nicht im Katalog stehen, sind als **Sonderwunsch** markiert. Bevor Sie Geräte zuweisen, entscheiden Sie:

- **Modell anlegen**: legt das Modell in den Stammdaten an und ordnet es zu.
- **Bestehendes Modell…** → **Zuordnen**: ordnet ein vorhandenes Modell zu.
- Menge beim Bestätigen auf 0 setzen, wenn der Wunsch entfällt.

## Geräte zuweisen

Nach dem Bestätigen weisen Sie jeder Position konkrete Geräte zu. Der Fortschritt steht oben, z. B. „3 von 5 bereit“.

- **Scannen:** Scannen Sie die Inventar- oder Seriennummer. Argus legt das Gerät automatisch in die passende offene Position. Eine Position für genau dieses Modell hat Vorrang vor einer „beliebiges Modell“-Position.
- **Von Hand:** Wählen Sie in einer Position ein Gerät aus der Liste der passenden Geräte im Lager.
- **Automatisch:** **Automatisch** füllt eine Position, **Alle automatisch zuteilen** die ganze Anforderung. Argus nimmt Geräte im besten Zustand zuerst. Sonderwünsche bleiben offen.

Zugewiesene Geräte haben den Status **Reserviert** und stehen nicht mehr für andere Anforderungen zur Verfügung. Eine Zuweisung entfernen Sie mit dem runden Button an der Position.

### Verbrauchsmaterial

Verbrauchsmaterial haken Sie ab (**Als bereitgelegt abhaken**). Die gesamte Menge kommt aus **einem** Lagerort. Liegen mehrere Lagerorte zur Wahl, wählen Sie einen. Reicht kein einzelner Lagerort, meldet Argus „Nicht genug auf Lager“.

Verbrauchsmaterial wird bei der Ausgabe ausgebucht und nicht zurückerwartet.

### Software

Für Softwarepositionen wählen Sie unter **Lizenz wählen…** eine Lizenz mit freien Plätzen. Bei Gerätelizenzen wählen Sie zusätzlich ein Gerät, das dem Mitarbeiter gehört.

Der Lizenzplatz wird sofort vergeben, nicht erst bei der Ausgabe. Die automatische Zuweisung verwendet nur Mitarbeiterlizenzen und bevorzugt die Lizenz, die zuerst abläuft.

Gibt es keine freie Lizenz, legen Sie eine an oder erhöhen die Plätze unter [Lizenzen](./licenses).

### Fehlende Geräte bestellen

Reicht der Bestand nicht, legt **Fehlendes bestellen** eine Bestellung für die offenen Positionen an. Beim Wareneingang werden die gelieferten Geräte dieser Anforderung direkt zugewiesen, siehe [Beschaffung](./procurement).

## Abholbereit melden

Sind alle Positionen zugewiesen, planen Sie mit **Abholbereit melden** die Übergabe.

| Art der Übergabe | Ablauf |
| --- | --- |
| **Abholung mit Unterschrift** | Der Mitarbeiter holt die Geräte am [Abholterminal](./terminal) ab und unterschreibt dort. |
| **Einfache Abholung** | Der Mitarbeiter holt die Geräte ohne Unterschrift ab. Die IT erfasst danach unter **Ausgeben**, wer sie entgegengenommen hat. |
| **Lieferung durch IT** | Die IT bringt die Geräte vorbei und erfasst danach die Ausgabe. |

Dazu legen Sie Termin und **Abholort** fest; bei einer Lieferung nur das Datum. Der Wunschtermin des Mitarbeiters steht im Dialog.

::: info Gut zu wissen
Vorgeschlagen wird die nächste volle Stunde. Die Uhrzeit wählen Sie im Feld neben dem Datum in Viertelstunden zwischen 6 und 20 Uhr. Gibt es nur einen Abholort, ist er bereits eingetragen.
:::

- **Mitarbeiter benachrichtigen**: Der Mitarbeiter erhält Termin und Ort. Dafür müssen Termin und Ort angegeben sein. Bei einer Direktausgabe ist diese Option standardmäßig aus.
- **Geräteprüfung am Terminal überspringen**: Das Terminal beginnt direkt mit „Wer holt ab?“.

Wer die Anforderung abholbereit meldet, steht als **Bereitgestellt von** auf der Anforderung und wird am Terminal als ausgebende Person vorgeschlagen.

Termin, Ort und Art ändern Sie später über **Übergabe ändern** (unter ⋮). Ist die Anforderung bereits abholbereit und die Benachrichtigung eingeschaltet, erfährt der Mitarbeiter von der Änderung.

**Zurück in Vorbereitung** (unter ⋮) nimmt die Anforderung vom Abholterminal. Die zugewiesenen Geräte bleiben erhalten.

::: info Gut zu wissen
- Entfernen Sie eine Zuweisung bei einer abholbereiten Anforderung, geht sie zurück auf **Bestätigt**.
- Enthält die Anforderung nur Software, heißt der Button **Lizenzen freigeben**. Die Anforderung gilt damit sofort als ausgegeben.
:::

## Ausgeben

**Ausgeben** erfasst die Übergabe durch die IT, ohne Unterschrift:

- **Entgegengenommen von**: standardmäßig der Mitarbeiter, sonst ein Kollege
- **Geliefert an**: bei Lieferungen, z. B. „Büro 2.14“
- **Hinweise pro Gerät** und **Notizen**, z. B. „Kratzer am Deckel“

Die Geräte gehören danach immer dem Mitarbeiter, der angefordert hat, auch wenn ein Kollege sie entgegennimmt.

Nach der Ausgabe:

- Befristete Anforderungen sind **Ausgegeben**, bis alles zurück ist.
- Dauerhafte Anforderungen sind sofort **Abgeschlossen**.
- Anforderungen nur mit Verbrauchsmaterial sind sofort **Abgeschlossen**.

Jede Übergabe hat ein druckbares **Übergabeprotokoll**. Sie öffnen es über die Karte **Übergabe**.

## Ohne erfasste Geräte ausgeben

Manchmal sind Geräte schon beim Mitarbeiter, bevor die IT sie in Argus erfasst hat. Dafür gibt es bei bestätigten Anforderungen **Als ausgegeben markieren**:

- Bereits zugewiesene Geräte werden normal ausgegeben.
- Offene Positionen bleiben offen. Die Anforderung zeigt dann **Geräte erfassen**.
- Ein später erfasstes Gerät gilt als seit der ursprünglichen Ausgabe beim Mitarbeiter.
- Der Mitarbeiter erhält keine Benachrichtigung.

Kommen die Geräte zurück, ohne dass sie erfasst wurden, schließt **Als zurückgegeben markieren** die offenen Positionen. Danach lassen sich keine Geräte mehr erfassen.

## Leihfrist verlängern

Bei ausgegebenen befristeten Anforderungen verlängert **Leihfrist verlängern** die Rückgabe, um 1, 2 oder 4 Wochen oder auf ein freies Datum. Die maximale Ausleihdauer gilt dabei nicht. Der Mitarbeiter wird benachrichtigt.

## Zurücknehmen

**Zurücknehmen** öffnet den Dialog **Rücknahme**:

1. Zurückgegebene Positionen auswählen.
2. Bei Bedarf den Zustand notieren, z. B. „Display gesprungen“.
3. Defekte Geräte als **Defekt** markieren. Sie gehen auf **In Reparatur** statt **Im Lager**.

Teilrückgaben sind möglich. Jede Rücknahme wird einzeln mit Datum und Person festgehalten. Lizenzplätze werden bei der Rücknahme frei. Ist alles zurück, ist die Anforderung **Abgeschlossen**.

Nehmen Sie ein Gerät auf seiner Geräteseite zurück, zählt das ebenfalls als Rückgabe auf der Anforderung.

## Überfällige Rückgaben

Eine befristete Anforderung ist überfällig, wenn das Rückgabedatum vorbei ist. Sie erscheint dann rot, im Filter **Überfällig**, auf dem Dashboard und im Kalender.

Argus erinnert den Mitarbeiter automatisch:

- **Rückgabe-Erinnerung**: einige Tage vorher (Standard: 2 Tage, siehe [Einstellungen](./administration/settings#fristen-vorwarnzeiten))
- **Rückgabe überfällig**: einmal, sobald das Datum überschritten ist

Beide gehen pro Rückgabedatum nur einmal raus. Nach einer Verlängerung erinnert Argus erneut.

Zusätzlich schickt **An Rückgabe erinnern** dem Mitarbeiter sofort eine E-Mail. Sie geht auch dann raus, wenn er Benachrichtigungen abgeschaltet hat. Voraussetzung sind ein eingerichteter E-Mail-Versand und eine E-Mail-Adresse beim Mitarbeiter.

## Im Namen eines Mitarbeiters anfordern

Unter **Neue Anforderung** fordern Sie Geräte aus dem Katalog an, für sich oder unter **Anforderung für Mitarbeiter** im Namen eines anderen. Erfasst die IT eine Anforderung für jemand anderen, entfällt die Genehmigung.

Bestimmte Geräte aus dem Lager stellen Sie über die [Direktausgabe](#direktausgabe) bereit.

## Direktausgabe

Unter **IT-Betrieb → Direktausgabe** (oder **Direkt ausgeben** in den Anforderungen) stellen Sie bestimmte Geräte aus dem Lager für einen Mitarbeiter bereit, ohne Anforderung und ohne Genehmigung. Der Menüpunkt erscheint nur mit Schreibrecht auf Anforderungen.

1. Geräte scannen oder suchen, Verbrauchsmaterial hinzufügen.
2. Mitarbeiter, Dauer und Zeitraum wählen.
3. Die Anforderung entsteht direkt als **Bestätigt** mit allen Geräten zugewiesen.
4. Weiter wie gewohnt mit **Abholbereit melden** und **Ausgeben** oder am Terminal.

In der Liste tragen Direktausgaben die Markierung **direkt**.

## Schnellzuweisung

Die schnellste Variante für ein einzelnes Gerät: **Schnellzuweisung** auf der Seite eines Geräts im Lager. Das Gerät ist sofort ausgegeben, siehe [Geräte](./devices#schnellzuweisung).

## Verlauf

Der **Verlauf** einer Anforderung zeigt jeden Schritt mit Datum und Person: Genehmigung, Bestätigung, Zuweisungen, Abholbereit-Meldung, Ausgabe, Verlängerungen, Erinnerungen und Rücknahmen. Mitarbeitende sehen nur die für sie relevanten Einträge.

::: info Gut zu wissen
- Meldet Argus „Das ist nicht möglich, solange die Anforderung … ist“, hat meist ein Kollege die Anforderung gleichzeitig bearbeitet. Laden Sie die Seite neu.
- Mitarbeitende können eine Anforderung stornieren, solange sie nicht ausgegeben ist, auch wenn sie schon abholbereit ist.
:::
