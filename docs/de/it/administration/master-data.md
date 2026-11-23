# Stammdaten

Unter **Stammdaten** pflegen Sie die Grundlagen, auf denen alles andere aufbaut. Wer welche Stammdaten sehen und ändern darf, legen die [Rollen](./roles) fest.

## Allgemein

- Ein Klick auf eine Zeile öffnet das Formular. **Anlegen + Neu** speichert und öffnet direkt ein leeres Formular für den nächsten Eintrag.
- Kategorien, Standorte und Abteilungen lassen sich mit **Als Baum** hierarchisch anzeigen.
- Ein Eintrag, der noch verwendet wird, lässt sich nicht löschen. Setzen Sie ihn stattdessen auf inaktiv, wo es das Feld **Aktiv** gibt.
- Auswahllisten in Formularen funktionieren auch für Benutzer, die einen Stammdatenbereich selbst nicht sehen dürfen.

## Empfohlene Reihenfolge

Für eine neue Instanz:

1. [Nummernserien](#nummernserien) prüfen
2. [Standorte](#standorte) mit Lagern und Abholorten
3. [Abteilungen](#abteilungen)
4. [Teams](#teams) der IT
5. [Hersteller](#hersteller) und [Lieferanten](#lieferanten)
6. [Kategorien](#kategorien)
7. [Modelle](#modelle)
8. [Mitarbeiter](#mitarbeiter), falls sie nicht per LDAP kommen

## Hersteller

Name, Website sowie Support-Adresse und -Telefon. Die Support-Kontakte erscheinen auf jeder Geräteseite.

Ein Hersteller mit Modellen lässt sich nicht löschen.

## Lieferanten

Name, Kundennummer und Kontaktdaten. Inaktive Lieferanten werden beim Bestellen aus dem Bedarf nicht angeboten.

Ein Lieferant mit Bestellungen lässt sich nicht löschen.

## Kategorien

Kategorien gruppieren Modelle, z. B. „Notebooks“ oder „Headsets“, und steuern viel Verhalten.

| Feld | Bedeutung |
| --- | --- |
| **Name (Plural)** | z. B. „Notebooks“ |
| **Einzelbezeichnung** | Im Self-Service als „Notebook · beliebiges Modell“ |
| **Typ** | **Hardware** oder **Software**. Unterkategorien haben denselben Typ wie die übergeordnete. |
| **Übergeordnet** | Für Unterkategorien |
| **Name der Kennung** | Wie das Feld „Kennung“ bei Geräten heißt, z. B. „CN“ |
| **Nummernserie** | Für die Inventarnummern neuer Geräte |
| **Name neuer Geräte** | **Kein Name**, **Aus einer Nummernserie** oder **Wie die Inventarnummer**, siehe [Gerätenamen](../devices#geratenamen) |
| **Zuständiges Team** | Erhält Anforderungen und Meldungen zu dieser Kategorie |
| **Im Portal anforderbar** | Erscheint im Self-Service |
| **Auswahl im Portal** | **Beliebiges oder bestimmtes Modell**, **Nur beliebiges Modell** oder **Nur bestimmtes Modell** |
| **Genehmigungspflichtig** | Anforderungen brauchen die Genehmigung der Abteilung |
| **Zubehör** | Erscheint im Self-Service als Zubehör zu passenden Modellen |

### Was Unterkategorien erben

| Einstellung | Vererbt? |
| --- | --- |
| Genehmigungspflichtig | Ja |
| Zubehör | Ja |
| Zuständiges Team | Ja, sofern die Unterkategorie keines hat |
| Komponenten | Ja |
| Nummernserie | **Nein** |
| Name neuer Geräte | **Nein** |
| Name der Kennung | **Nein** |

::: warning Achtung
Nummernserien werden nicht vererbt. Eine Unterkategorie ohne eigene Serie bekommt Nummern aus der allgemeinen Inventarserie (`INV-000001`). Hinterlegen Sie die Serie deshalb bei jeder Kategorie, die Geräte enthält, oder direkt am Modell.
:::

### Komponenten

Unter **Stammdaten → Komponenten** legen Sie austauschbare Teile an, z. B. „Akku“, und ordnen sie Kategorien zu. Geräte dieser Kategorien und ihrer Unterkategorien erhalten dann Felder für Seriennummer und Einbaudatum des Teils.

## Modelle

| Feld | Bedeutung |
| --- | --- |
| **Name**, **Herstellerbezeichnung**, **Hersteller**, **Kategorie** | Pflicht. Die Herstellerbezeichnung ist je Hersteller eindeutig. |
| **Führung** | **Einzelgeräte**, **Verbrauchsmaterial (Menge)** oder **Softwarelizenz**. Software-Kategorien enthalten nur Lizenzen. |
| **Artikelnummer**, **EAN / GTIN** | Ein Scan dieser Nummern findet das Modell. |
| **Nummernserie** | Für Inventarnummern; hat Vorrang vor der Serie der Kategorie |
| **Standardlieferant**, **Listenpreis** | Vorbelegung beim Bestellen |
| **Garantie (Monate)** | Garantieende beim Wareneingang (Standard 24) |
| **Zuständiges Team** | Hat Vorrang vor dem Team der Kategorie |
| **Im Portal anforderbar** | Erscheint im Self-Service |
| **Nachfolger von** | Verknüpft Modellgenerationen |
| **Kompatibel mit** | Passendes Zubehör und Verbrauchsmaterial, in beide Richtungen |

**Nachfolger anlegen** (im Menü einer Zeile) legt ein neues Modell an und übernimmt Hersteller, Kategorie, Führung, Nummernserie, Lieferant, Garantie, Team, Portal-Einstellung und Kompatibilität.

Ein Modell, zu dem Geräte, Bestände, Lizenzen, Bestellungen oder Anforderungen existieren, lässt sich nicht löschen. Setzen Sie es auf inaktiv.

## Standorte

Standorte bilden eine Hierarchie, z. B. „München / Haus A / Raum 2.14“. **Art**: **Standort**, **Gebäude**, **Raum** oder **Lager**.

**Abholort** macht einen Standort beim Abschließen der Vorbereitung als Abholort wählbar.

Ein Standort mit untergeordneten Standorten oder Verbrauchsmaterial-Bestand lässt sich nicht löschen.

## Abteilungen

Abteilungen bilden ebenfalls eine Hierarchie. Wichtigstes Feld sind die **Genehmiger**: Sie genehmigen Anforderungen der Abteilung. Für ihre Abwesenheit tragen Genehmiger selbst eine [Vertretung](../../approvers/delegation) ein; die IT muss dafür nichts ändern. Alle Vertretungen sieht ein Administrator im Django-Admin.

Hat eine Abteilung keine eigenen Genehmiger, gelten die der nächsthöheren Abteilung. Die Liste zeigt sie mit dem Hinweis „Übernommen von der übergeordneten Abteilung“.

::: warning Achtung
Gibt es in der ganzen Hierarchie keinen Genehmiger, gehen genehmigungspflichtige Anforderungen ohne Hinweis direkt an die IT.
:::

## Teams

Teams gliedern die IT, z. B. „Arbeitsplatz“ und „Mobile Geräte“. Kategorien und Modelle verweisen auf ein **zuständiges Team**; neue Anforderungen und Meldungen gehen dann an dieses Team.

- **Mitglieder**: nur IT-Mitarbeitende
- **Standard-Team**: erhält alles, wofür kein anderes Team zuständig ist. Es gibt höchstens eines.
- **LDAP-Gruppe**: Mit LDAP gleicht Argus die Mitglieder bei jeder Anmeldung mit dieser Gruppe ab.

## Mitarbeiter

| Bereich | Felder |
| --- | --- |
| **Person** | Vorname, Nachname, E-Mail, Telefon |
| **Organisation** | Abteilung, Position, Personalnummer, **Von Genehmigungen befreit** |
| **Konto** | Benutzername, Aktiv, **Darf Passwort ändern**, **Sitzungsdauer (Stunden)**, Passwort setzen, Zwei-Faktor-Anmeldung zurücksetzen |
| **Berechtigungen** | **IT-Mitarbeiter**, **Administrator**, Teams, Rollen |
| **Abholterminal** | Konto für das [Abholterminal](../terminal) und dessen Standort |

Die Spalte **Konto** zeigt Kennzeichen wie **Admin**, **IT**, **Terminal**, **LDAP** und **2FA**.

::: info Gut zu wissen
- In Argus angelegte Benutzer haben zunächst kein Passwort. Sie melden sich per LDAP an, oder ein Administrator setzt im Bereich **Konto** mit **Passwort setzen** eines, siehe [Passwörter lokaler Konten](./sign-in#passworter-lokaler-konten).
- Mitarbeitende mit Anforderungen oder zugewiesenen Geräten lassen sich nicht löschen. Deaktivieren Sie sie stattdessen; sie können sich dann nicht mehr anmelden.
- Das eigene Konto kann niemand deaktivieren oder löschen und niemand sich selbst die Administratorrechte entziehen.
:::

## Nummernserien

Aus Nummernserien vergibt Argus fortlaufende Nummern: Inventarnummern, Gerätenamen, Anforderungs- und Bestellnummern.

| Feld | Bedeutung |
| --- | --- |
| **Präfix** | Wird für `{prefix}` eingesetzt |
| **Muster** | Aufbau der Nummer, z. B. `{prefix}{year}-{seq}` |
| **Stellen** | Mindestlänge der laufenden Nummer, mit Nullen aufgefüllt |
| **Neustart** | **Nie**, **Jährlich** oder **Monatlich** |
| **Nächster Wert** | Die nächste laufende Nummer |

Platzhalter im Muster:

| Platzhalter | Ergebnis |
| --- | --- |
| `{prefix}` | Das Präfix |
| `{year}` | Jahr, vierstellig |
| `{yy}` | Jahr, zweistellig |
| `{month}` | Monat, zweistellig |
| `{seq}` | Laufende Nummer (Pflicht) |

Die Vorschau im Formular zeigt Beispielnummern.

### System-Serien

Drei Serien gehören Argus selbst und lassen sich ändern, aber nicht löschen:

| Serie | Standard | Beispiel |
| --- | --- | --- |
| Inventarnummern | `INV-{seq}`, 6 Stellen | `INV-000042` |
| Anforderungen | `RES-{year}-{seq}`, 5 Stellen, jährlich neu | `RES-2026-00017` |
| Bestellungen | `PO-{year}-{seq}`, 4 Stellen, jährlich neu | `PO-2026-0003` |

### Eigene Serien

Eigene Serien ordnen Sie zu:

- einer **Kategorie** oder einem **Modell** für Inventarnummern, z. B. `NB-{seq}` für Notebooks
- einer **Kategorie** unter **Name neuer Geräte** für Gerätenamen, z. B. `pc-{seq}` oder `H{seq}`

::: info Gut zu wissen
- Bereits vergebene Nummern überspringt Argus, z. B. nach einer Eingabe von Hand.
- Bei jährlichem oder monatlichem Neustart beginnt die Zählung mit der ersten Nummer im neuen Zeitraum wieder bei 1.
- Eine Serie, die eine Kategorie für Gerätenamen verwendet, lässt sich nicht löschen.
:::
