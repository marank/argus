# Verbrauchsmaterial

Unter **IT-Betrieb → Verbrauchsmaterial** führen Sie Material nach Menge statt nach Einzelgerät: Tinte, Toner, Akkus, Kabel, Zubehör.

## Grundprinzip

Jeder Eintrag ist ein Artikel an einem Lagerort. Liegt derselbe Toner in zwei Lagern, sind das zwei Einträge mit eigenem Bestand.

| Spalte | Bedeutung |
| --- | --- |
| **Bestand** | Was physisch da ist. Der Balken wird orange, wenn der Bestand unter den Mindestbestand fällt. |
| **Reserviert** | Für Anforderungen zurückgelegt |
| **Verfügbar** | Bestand minus Reserviert |
| **Mindestbestand** | Darunter gilt der Artikel als knapp |

## Neuen Artikel anlegen

1. Das Modell in den [Stammdaten](./administration/master-data#modelle) mit der Führung **Verbrauchsmaterial (Menge)** anlegen.
2. **Neues Verbrauchsmaterial**: Modell, Standort und Mindestbestand wählen.
3. Den Bestand über **Einbuchen** erfassen. Ein neuer Eintrag beginnt bei 0.

## Buchen

Im Menü jeder Zeile:

| Aktion | Wofür |
| --- | --- |
| **Einbuchen** | Zugang, z. B. Lieferung |
| **Ausbuchen** | Abgang, optional mit Empfänger |
| **Korrigieren** | Neuen Zählstand eintragen, z. B. nach einer Inventur |
| **Bewegungen** | Die letzten 200 Buchungen mit Grund, Empfänger und Notiz |

Ausbuchen und Korrigieren nach unten betreffen nur die verfügbare Menge. Für Anforderungen reservierte Stück sind gesperrt.

Bewegungsarten: **Wareneingang**, **Ausgabe**, **Korrektur** und **Für Reparatur verbraucht** (über [Service erfassen](./devices#servicebuch)).

## Über Anforderungen

- Beim Zuweisen wird die Menge **reserviert**. Der Bestand bleibt, bis die Ausgabe erfolgt.
- Bei der Ausgabe wird ausgebucht, mit dem Mitarbeiter als Empfänger und der Anforderungsnummer als Notiz.
- Verbrauchsmaterial wird nicht zurückerwartet.
- Storno oder Entfernen der Zuweisung gibt die Reservierung frei.

## Passendes Material

Am Modell legen Sie unter **Kompatibel mit** fest, welches Material zu welchem Gerät passt, z. B. die Tintenpatrone zum Drucker. Die Zuordnung gilt in beide Richtungen. Einzelnen Geräten können Sie zusätzlich Material zuordnen.

Mitarbeitende sehen passendes Material zu ihren eigenen Geräten im Self-Service unter **Passend zu Ihren Geräten**.

## Knappe Bestände

- Filter **Nur unter Mindestbestand** in der Liste
- Dashboard-Widget **Verbrauchsmaterial knapp**
- **Beschaffung → Bedarf** listet alle knappen Artikel zum Bestellen

Knapp ist ein Artikel, wenn der Bestand **unter** dem Mindestbestand liegt. Bei genau dem Mindestbestand gilt er noch nicht als knapp. Eine E-Mail-Warnung gibt es nicht.
