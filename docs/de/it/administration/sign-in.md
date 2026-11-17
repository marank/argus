# Anmeldung und Sicherheit

## Anmelden

Alle melden sich auf derselben Seite mit Benutzername und Passwort an, lokale Konten wie LDAP-Konten. Groß- und Kleinschreibung des Benutzernamens spielt keine Rolle.

Eine Anmeldung gilt standardmäßig 12 Stunden. Danach meldet Argus „Ihre Sitzung ist abgelaufen“.

- **Für alle:** unter **Einstellungen → Fristen & Vorwarnzeiten → Sitzungsdauer**, siehe [Einstellungen](./settings#anmeldung).
- **Für einzelne Konten:** unter **Stammdaten → Mitarbeiter** im Feld **Sitzungsdauer (Stunden)**, z. B. länger für das Abholterminal. Leer bedeutet: Wert aus den Einstellungen.

Eine geänderte Dauer gilt ab der nächsten Anmeldung.

## Sperre nach Fehlversuchen

| Grenze | Sperre |
| --- | --- |
| 10 falsche Passwörter für einen Benutzernamen | 15 Minuten |
| 30 falsche Passwörter von einer Adresse | 15 Minuten |
| 10 falsche Codes im zweiten Schritt | 15 Minuten |

Eine erfolgreiche Anmeldung setzt den Zähler des Kontos zurück. Sofort entsperrt ein Administrator ein Konto, indem er ein neues Passwort setzt.

## Passwörter lokaler Konten

Lokale Konten sind Konten ohne LDAP, z. B. der erste Administrator, Terminal-Konten oder Mitarbeitende, die nicht im Verzeichnis stehen. LDAP-Benutzer ändern ihr Passwort im Verzeichnis.

### Passwort selbst ändern

Im Benutzermenü unter **Anmeldung & Sicherheit → Passwort ändern**: aktuelles Passwort, dann das neue zweimal. Die aktuelle Sitzung bleibt angemeldet, alle anderen Sitzungen des Kontos enden.

Ob jemand sein Passwort selbst ändern darf, steuert der Haken **Darf Passwort ändern** am Mitarbeiter (standardmäßig an). Für gemeinsam genutzte Konten wie das Abholterminal schalten Sie ihn aus.

### Passwort setzen durch Administratoren

Unter **Stammdaten → Mitarbeiter** zeigt der Bereich **Konto**, ob ein Passwort gesetzt ist. Mit **Passwort setzen** vergibt ein Administrator ein neues Passwort, z. B. für ein neu angelegtes Konto oder wenn jemand sein Passwort vergessen hat.

- Das Passwort gilt sofort; bestehende Sitzungen des Kontos enden.
- Eine Sperre nach Fehlversuchen wird dabei aufgehoben.
- Das eigene Passwort ändern Administratoren im Profil, nicht hier.

### Regeln

Neue Passwörter haben mindestens 8 Zeichen, bestehen nicht nur aus Ziffern, sind kein gängiges Passwort und ähneln nicht dem Namen des Benutzers.

Ein neu angelegtes Konto hat zunächst kein Passwort. Es kann sich erst anmelden, wenn ein Administrator eines setzt oder LDAP eingerichtet ist.

## Zwei-Faktor-Anmeldung

Jeder Benutzer kann im Benutzermenü unter **Anmeldung & Sicherheit** einen zweiten Anmeldeschritt einrichten. Einrichten, Wechseln und Abschalten verlangen das Passwort.

| Methode | Ablauf |
| --- | --- |
| **Authenticator-App** (empfohlen) | QR-Code mit einer App wie Microsoft Authenticator oder 1Password scannen. Bei der Anmeldung den 6-stelligen Code eingeben. |
| **Code per E-Mail** | Argus schickt bei der Anmeldung einen Code, 10 Minuten gültig. Nur verfügbar mit E-Mail-Adresse und eingerichtetem E-Mail-Versand. |

### Backup-Codes

Beim Einrichten zeigt Argus einmalig zehn **Backup-Codes**. Jeder gilt einmal und ersetzt den Code, wenn Telefon oder Postfach nicht zur Hand sind. Speichern Sie sie sicher: kopieren oder als Textdatei.

Sind nur noch wenige übrig, warnt Argus. **Neue Codes erzeugen** ersetzt alle bisherigen.

### Zugang verloren

Ohne Telefon und ohne Backup-Codes setzt die IT die Zwei-Faktor-Anmeldung zurück: **Stammdaten → Mitarbeiter**, Benutzer öffnen, unter **Zwei-Faktor-Authentifizierung** auf **Zurücksetzen**.

- Prüfen Sie vorher die Identität der anfragenden Person.
- Das geht nicht für das eigene Konto.
- Die Anmeldung eines Administrators setzt nur ein Administrator zurück.

::: warning Achtung
Fällt der E-Mail-Versand aus, kommen Benutzer mit **Code per E-Mail** nur noch mit Backup-Codes hinein. Empfehlen Sie deshalb die Authenticator-App.
:::

Der Django-Admin nutzt dieselbe Anmeldung, inklusive zweitem Schritt.

## Darstellung und Sprache

Im Benutzermenü wählt jeder:

- **Sprache**: Deutsch oder English. Auch E-Mails kommen in dieser Sprache.
- **Darstellung**: System, Hell, Solarized, Dunkel oder Retro. **System** folgt der Einstellung des Geräts.

Beides wird im Konto gespeichert und gilt auf allen Geräten.
