# Scannen

Argus arbeitet mit jedem Barcode-Scanner, der wie eine Tastatur eingibt. Eine Einrichtung ist nicht nötig.

## Überall in den IT-Ansichten

Ein Scan funktioniert auf jeder Seite, auch ohne vorher ins Suchfeld zu klicken. Alternativ tippen Sie die Nummer oben in das Feld **Scannen**.

| Gescannt | Ergebnis |
| --- | --- |
| Inventarnummer, Seriennummer, Kennung, IMEI, MAC-Adresse | Die Geräteseite öffnet sich |
| Seriennummer eines eingebauten Teils, z. B. Akku | Die Seite des Geräts, in dem das Teil steckt |
| EAN oder Artikelnummer | Die Geräteliste, gefiltert auf das Modell |

Gibt es mehrere Treffer, wählen Sie aus einer Liste. Ohne Treffer meldet Argus „Kein Treffer für …“.

::: info Gut zu wissen
- Steht der Cursor in einem Eingabefeld, landet der Scan in diesem Feld.
- Hat eine Seite ein eigenes Scanfeld, z. B. bei der Gerätezuweisung, gehen Scans dorthin.
- Argus erkennt einen Scan an der schnellen Eingabe mit abschließendem Enter. Sehr kurze Codes unter 5 Zeichen fängt Argus nicht ab; geben Sie diese ins Scanfeld ein.
:::

## Mehrere Geräte nacheinander

| Wo | Was passiert |
| --- | --- |
| [Gerätezuweisung](./requests#gerate-zuweisen) einer Anforderung | Jedes gescannte Gerät kommt in die passende offene Position. |
| [Direktausgabe](./requests#direktausgabe) | Jedes gescannte Gerät kommt in den Warenkorb. |
| **Geräte → Mehrere einscannen** | Seriennummern neuer Geräte eines Modells, eine pro Scan |
| [Wareneingang](./procurement#wareneingang) | Seriennummern gelieferter Geräte |

Bei der Gerätezuweisung und der Direktausgabe erkennt Argus nur Inventar- und Seriennummern. Haben mehrere Geräte dieselbe Seriennummer, scannen Sie die Inventarnummer.
