# Abholung am Terminal

Das Abholterminal ist ein gemeinsam genutzter Touch-PC, an dem Mitarbeitende vorbereitete Geräte prüfen und die Übergabe unterschreiben.

## Einsatzarten

| Einsatz | Ablauf |
| --- | --- |
| **Übergabe mit der IT** | Mitarbeiter und IT gehen die Abholung gemeinsam am Terminal durch. Die IT erklärt die Geräte, beide prüfen sie, der Mitarbeiter unterschreibt. |
| **Selbstabholung** | Der Mitarbeiter holt die vorbereiteten Geräte allein ab, z. B. aus einem Abholregal, und unterschreibt ohne die IT. |

Der Ablauf am Terminal ist in beiden Fällen gleich. Bei der Übergabe mit der IT wählt diese im letzten Schritt unter **Ändern** sich selbst als ausgebende Person, wenn jemand anderes die Anforderung vorbereitet hat.

## Einrichtung

1. Unter **Stammdaten → Mitarbeiter** ein Konto für das Terminal anlegen, **Abholterminal** aktivieren, **Darf Passwort ändern** ausschalten und eine längere **Sitzungsdauer (Stunden)** eintragen.
2. Optional unter **Standort des Terminals** einen Standort wählen. Das Terminal zeigt dann nur Abholungen an diesem Standort und den Standorten darunter. Ohne Standort zeigt es alle.
3. Dem Konto ein Passwort geben, siehe [Passwörter lokaler Konten](./administration/sign-in#passworter-lokaler-konten).
4. Am Touch-PC mit diesem Konto anmelden.

Ein Terminal-Konto sieht ausschließlich die Abholungen, keine anderen Bereiche von Argus, und erhält keine Benachrichtigungen. IT-Mitarbeitende können das Terminal zum Testen ebenfalls öffnen.

::: warning Achtung
Eine Anmeldung gilt standardmäßig 12 Stunden. Damit das Terminal nicht täglich neu angemeldet werden muss, tragen Sie am Terminal-Konto eine längere **Sitzungsdauer (Stunden)** ein, z. B. 168 für eine Woche.
:::

Das Modul **Abholterminal** muss in den [Einstellungen](./administration/settings) eingeschaltet sein.

## Welche Abholungen erscheinen

Das Terminal listet alle Anforderungen, die **Abholbereit** sind und als Übergabeart **Abholung mit Unterschrift** haben. Die nächste Abholung steht oben. Die Liste aktualisiert sich selbst.

Gesucht wird nach Name oder Anforderungsnummer; ein Tipp auf den Namen startet die Abholung.

## Ablauf

### 1. Geräte prüfen

Der Mitarbeiter sieht alle Geräte und Artikel der Anforderung, mit Rückgabedatum oder **Dauerhaft**. Hat die IT einen Vermerk hinterlegt, erscheint er hier.

Stimmt etwas nicht, z. B. ein sichtbarer Schaden, erfasst der Mitarbeiter pro Gerät einen **Hinweis**. Unter **Weitere Anmerkungen** ist Platz für alles Übrige. Weiter mit **Alles geprüft**.

Hat die IT die Geräteprüfung übersprungen, beginnt das Terminal mit Schritt 2.

### 2. Wer holt ab?

- **Ich bin {Name}**: Der Mitarbeiter holt selbst ab.
- **Jemand anderes**: Ein Kollege holt in Vertretung ab. Er sucht sich nach Name oder Personalnummer. Findet er sich nicht, wird der eingegebene Name übernommen.

Die Geräte werden in jedem Fall dem Mitarbeiter zugeordnet, der sie angefordert hat.

### 3. Unterschreiben

Das Terminal zeigt, wer die Geräte entgegennimmt und wer aus der IT sie ausgibt. Vorgeschlagen ist die Person, die die Anforderung abholbereit gemeldet hat; über **Ändern** lässt sich jemand anderes aus der IT wählen. Im Protokoll steht die hier gewählte Person.

Der Mitarbeiter unterschreibt im Feld und tippt auf **Unterschreiben und abschließen**. Die Anforderung ist damit ausgegeben; der Mitarbeiter erhält eine Bestätigung.

::: info Gut zu wissen
- Nach 2 Minuten ohne Eingabe kehrt das Terminal zur Liste zurück. Begonnene Eingaben gehen verloren.
- **Abbrechen** verwirft eine begonnene Abholung nach Rückfrage.
- Lizenzen erscheinen nicht in der Geräteprüfung; sie werden mit der Abholung trotzdem übergeben.
:::

## Übergabeprotokoll

Jede Übergabe hat ein Protokoll im A4-Format. Die IT öffnet es auf der Anforderung über die Karte **Übergabe** und druckt es mit **Drucken**.

Das Protokoll enthält:

- Mitarbeiter, Abteilung, Zweck und Zeitraum
- Art der Übergabe, Empfänger, ausgebende Person und das erfassende Konto (z. B. das Terminal)
- alle Geräte mit Inventarnummer, Modell, Seriennummer und Hinweisen
- die Unterschrift, bei einer Ausgabe ohne Terminal eine leere Unterschriftszeile
- spätere Rücknahmen mit Defekt-Vermerken

Mitarbeitende sehen die Übergabe auf ihrer Anforderung, das Protokoll selbst nur die IT.
