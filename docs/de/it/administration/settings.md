# Einstellungen

Unter **Administration → Einstellungen** konfigurieren Administratoren Argus für alle Benutzer. Die Seite hat fünf Bereiche:

1. Module & Funktionen
2. Fristen & Vorwarnzeiten
3. [E-Mail](./email#e-mail-versand-einrichten)
4. [Benachrichtigungen](./email#benachrichtigungen-fur-alle-festlegen)
5. [LDAP-Anmeldung](./ldap)

## Module & Funktionen

Schalter wirken sofort, ohne Speichern. Standardmäßig ist alles eingeschaltet.

### Module

| Modul | Was wegfällt, wenn es aus ist |
| --- | --- |
| **Verbrauchsmaterial** | Verbrauchsmaterial-Verwaltung und Schnellwahl im Self-Service |
| **Software & Lizenzen** | Lizenzen, **Meine Software**, Lizenzwarnungen |
| **Beschaffung** | Bedarf und Bestellungen |
| **Kalender** | Der Kalender der IT |
| **Problemmeldungen** | Meldungen in IT und Self-Service, **Problem melden** |
| **Abholterminal** | Das Abholterminal |

Abgeschaltete Bereiche verschwinden aus Menüs und Seiten. Die Daten bleiben erhalten; nach dem Wiedereinschalten ist alles wieder da.

### Funktionen

| Funktion | Wirkung | Braucht |
| --- | --- | --- |
| **Garantieende im Kalender** | Ein Sammeleintrag pro Tag | Kalender |
| **Lizenzablauf im Kalender** | Enddaten befristeter Lizenzen | Kalender, Lizenzen |
| **Lieferungen im Kalender** | Erwartete Liefertermine | Kalender, Beschaffung |
| **Schnellwahl Verbrauchsmaterial** | Passendes Material zu den eigenen Geräten beim Anfordern | Verbrauchsmaterial |
| **Software anfordern** | Software-Kategorien im Self-Service | Lizenzen |
| **Hinweis-Animationen** | Pulsierende Markierungen an Elementen, die auf Bearbeitung warten | – |

Eine Funktion wirkt nur, solange alle Module eingeschaltet sind, die sie braucht. Sonst ist sie ausgegraut.

## Fristen & Vorwarnzeiten

### Ausleihen

Gilt für befristete Anforderungen.

| Einstellung | Standard | Wirkung |
| --- | --- | --- |
| **Standard-Ausleihdauer** | 5 Tage | Vorgeschlagener Zeitraum beim Anfordern, inklusive Starttag |
| **Maximale Ausleihdauer** | 0 = unbegrenzt | Längere Zeiträume lehnt Argus beim Anfordern, bei Direktausgaben und Schnellzuweisungen ab. Verlängerungen durch die IT sind nicht begrenzt. |
| **Rückgabe-Erinnerung** | 2 Tage | So viele Tage vor dem Rückgabedatum erinnert Argus den Mitarbeiter. 0 = am Rückgabetag. |

### Vorwarnzeiten

Ab wann Garantien und Lizenzen als „läuft bald ab“ gelten.

| Einstellung | Standard | Wirkung |
| --- | --- | --- |
| **Garantie** | 60 Tage | Dashboard und Widgets |
| **Lizenzen** | 60 Tage | Dashboard, Liste und Benachrichtigung **Lizenz läuft ab** |

### Anmeldung

| Einstellung | Standard | Wirkung |
| --- | --- | --- |
| **Sitzungsdauer** | 12 Stunden | So lange gilt eine Anmeldung (1 bis 720 Stunden). Gilt ab der nächsten Anmeldung; ein eigener Wert am Mitarbeiter hat Vorrang. |
