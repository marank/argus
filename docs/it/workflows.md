# Abläufe im Überblick

Die zentralen Abläufe in Argus. Die Details stehen auf den verlinkten Seiten.

## Von der Anforderung zur Rückgabe

| Schritt | Wer | Status danach |
| --- | --- | --- |
| [Anforderung absenden](../employees/request) | Mitarbeiter | **In Genehmigung** oder **Eingereicht** |
| [Genehmigen](../approvers/approvals), falls nötig | Genehmiger | **Eingereicht** |
| [Bestätigen](./requests#bestatigen) | IT | **Bestätigt** |
| [Geräte zuweisen](./requests#gerate-zuweisen) | IT | **Bestätigt**, Geräte reserviert |
| [Abholbereit melden](./requests#abholbereit-melden) | IT | **Abholbereit** |
| [Abholen](./terminal) oder [Ausgeben](./requests#ausgeben) | Mitarbeiter oder IT | **Ausgegeben** (befristet) oder **Abgeschlossen** (dauerhaft) |
| [Zurücknehmen](./requests#zurucknehmen), bei befristeten | IT | **Abgeschlossen** |

Abkürzungen: Die [Direktausgabe](./requests#direktausgabe) überspringt Anforderung und Genehmigung, die [Schnellzuweisung](./devices#schnellzuweisung) gibt ein einzelnes Gerät sofort aus.

## Vom Bedarf zum Gerät

1. **Bedarf erkennen**: Eine Anforderung kann nicht aus dem Lager bedient werden, oder Verbrauchsmaterial fällt unter den Mindestbestand.
2. **Bestellung anlegen** und **als bestellt markieren**.
3. **Wareneingang buchen**: Geräte entstehen und gehen direkt an die wartende Anforderung.

Siehe [Beschaffung](./procurement).

## Vom Problem zur Lösung

1. **Mitarbeiter meldet** ein Problem unter **Meine Geräte**. Das zuständige Team wird benachrichtigt.
2. **IT nimmt in Bearbeitung** und klärt per Nachricht.
3. **Gelöst**: IT oder Mitarbeiter schließen die Meldung.

Bei Bedarf wird das Gerät [ersetzt](./devices#gerat-ersetzen) oder repariert. Siehe [Probleme melden](../employees/report-issue) und [Meldungen](./issues).

## Ein Gerät im Lauf der Zeit

**Im Lager** → **Reserviert** → **In Benutzung** → **Im Lager** → … → **Ausgemustert**

Zwischendurch kann ein Gerät **In Reparatur** gehen und danach zurück ins Lager. Jeder Schritt steht im [Servicebuch](./devices#servicebuch) des Geräts.
