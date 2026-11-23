# E-Mail und Benachrichtigungen

Argus benachrichtigt auf zwei Wegen: per **E-Mail** und **in der App** über die Glocke oben rechts. Administratoren legen fest, was es grundsätzlich gibt; jeder Benutzer kann für sich einzelne Benachrichtigungen abschalten.

## E-Mail-Versand einrichten

Unter **Einstellungen → E-Mail**:

| Feld | Bedeutung |
| --- | --- |
| **E-Mails senden** | Hauptschalter, standardmäßig aus |
| **Server** | SMTP-Server |
| **Port & Verschlüsselung** | **STARTTLS** (meist Port 587), **SSL/TLS** (meist Port 465) oder **Keine**. Den Port passen Sie selbst an. |
| **Benutzername**, **Passwort** | Anmeldung am Server. Ein leeres Passwortfeld behält das gespeicherte Passwort. |
| **Absenderadresse**, **Absendername** | So erscheinen die Mails beim Empfänger |
| **App-Adresse** | Adresse von Argus, z. B. `https://argus.firma.de`. Ohne sie enthalten Mails keine Links. |

Speichern Sie zuerst und senden Sie dann unter **Testmail senden** eine Testmail. Die Testmail geht auch bei abgeschaltetem Hauptschalter raus; Fehler des Servers zeigt Argus direkt an.

::: info Gut zu wissen
- Mails gehen in der Sprache des Empfängers raus.
- Ist der Mailserver vorübergehend nicht erreichbar, versucht Argus es etwa einen Tag lang erneut.
- Schalten Sie **E-Mails senden** aus, verschickt Argus auch bereits wartende Mails nicht mehr.
- Das SMTP-Passwort steht in der Datenbank und damit auch in den Sicherungen.
:::

## Benachrichtigungen für alle festlegen

Unter **Einstellungen → Benachrichtigungen** schalten Sie jede Benachrichtigung pro Kanal (E-Mail, In der App) ein oder aus, getrennt nach Empfängern. Standardmäßig ist alles eingeschaltet.

### An Mitarbeiter

| Benachrichtigung | Wann |
| --- | --- |
| **Anforderung bestätigt** | Die IT hat bestätigt, mit Kommentar |
| **Anforderung abgelehnt** | Die IT oder der Genehmiger hat abgelehnt, mit Begründung |
| **Von der IT storniert** | Die IT hat die Anforderung storniert |
| **Geräte bereit** | Mit Termin und Ort; die IT kann sie im Einzelfall weglassen |
| **Übergabe geändert** | Termin, Ort oder Art haben sich nach Abschluss der Vorbereitung geändert |
| **Ausgegeben** | Was ausgegeben wurde und bis wann es zurück muss |
| **Leihfrist verlängert** | Mit neuem Rückgabedatum |
| **Zurückgenommen** | Was zurückgenommen wurde und was noch aussteht |
| **Rückgabe-Erinnerung** | Einige Tage vor der Rückgabe |
| **Rückgabe überfällig** | Einmal, sobald die Rückgabe überfällig ist |
| **Nachricht zu Problemmeldung** | Die IT hat zu einer Meldung geschrieben |
| **Problemmeldung gelöst** | Mit der Nachricht der IT |

### An die IT

| Benachrichtigung | Wann |
| --- | --- |
| **Neue Anforderung** | Eine Anforderung ist bei der IT eingegangen |
| **Neue Problemmeldung** | Ein Mitarbeiter hat ein Problem gemeldet |
| **Rückmeldung zu Problemmeldung** | Der Melder hat geschrieben oder die Meldung als gelöst markiert |
| **Mir zugewiesen** | Jemand hat Ihnen eine Anforderung oder Meldung zugewiesen |
| **Lizenz läuft ab** | Eine befristete Lizenz endet innerhalb der Vorwarnzeit |

Neue Anforderungen und Meldungen gehen an das zuständige Team, sonst an alle IT-Mitarbeiter.

### An Genehmiger

| Benachrichtigung | Wann |
| --- | --- |
| **Genehmigung erforderlich** | Eine Anforderung aus der Abteilung wartet auf Genehmigung. Geht auch an eine laufende Vertretung. |

### Erinnerung durch die IT

**An Rückgabe erinnern** auf einer Anforderung schickt dem Mitarbeiter sofort eine E-Mail. Sie geht unabhängig von allen Schaltern raus.

## Benachrichtigungen für sich selbst einstellen

Jeder Benutzer wählt im Benutzermenü unter **Benachrichtigungen**, welche Benachrichtigungen er per E-Mail und in der App erhält. Abschalten lässt sich nur, was ein Administrator eingeschaltet hat.

- Ohne eigene E-Mail-Adresse oder ohne eingerichteten E-Mail-Versand sind die E-Mail-Schalter gesperrt. Die eigene Adresse pflegt die IT oder das LDAP.
- IT-Benachrichtigungen sieht nur die IT, Genehmiger-Benachrichtigungen nur Genehmiger.

Inaktive Benutzer und Terminal-Konten erhalten nie Benachrichtigungen. Gelesene Benachrichtigungen in der App löscht Argus nach 90 Tagen.
