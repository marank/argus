# LDAP-Anmeldung

Mitarbeitende melden sich mit ihrem Verzeichniskonto an (LDAP oder Active Directory). Name, Personalnummer und weitere Angaben übernimmt Argus bei jeder Anmeldung aus dem Verzeichnis.

Lokale Konten wie der erste Administrator und das Abholterminal können sich immer anmelden, mit oder ohne LDAP.

## Einrichten

Unter **Einstellungen → LDAP-Anmeldung** (nur Administratoren). Alternativ setzen Sie die Werte als [Umgebungsvariablen](../operations/configuration#ldap-und-active-directory); diese haben Vorrang und erscheinen in Argus schreibgeschützt.

### Server

| Feld | Bedeutung |
| --- | --- |
| **Server-URI** | z. B. `ldaps://dc1.firma.de:636`. Mehrere Server kommagetrennt; Argus versucht sie der Reihe nach. |
| **StartTLS** | `ldap://`-Verbindungen auf TLS hochstufen |
| **Zertifikat prüfen** | Standardmäßig an |
| **CA-Zertifikatsdatei** | Pfad zu einer PEM-Datei im Container, für eine interne CA |
| **Timeout (s)** | Standard 5 |

### Benutzersuche

Argus sucht den Benutzer mit einem Dienstkonto und prüft das Passwort, indem es sich als dieser Benutzer anmeldet.

| Feld | Bedeutung |
| --- | --- |
| **Bind-DN**, **Bind-Passwort** | Dienstkonto. Leer = anonyme Suche. |
| **Suchbasis** | z. B. `OU=Staff,DC=firma,DC=de` |
| **Benutzerfilter** | Standard: `(&(objectClass=user)(sAMAccountName={username}))` |

Ändern Sie Server, Bind-DN oder Zertifikatseinstellungen, geben Sie das Bind-Passwort erneut ein.

### Feldzuordnung

| Argus-Feld | Standard-Attribut |
| --- | --- |
| Benutzername | `sAMAccountName` |
| Vorname | `givenName` |
| Nachname | `sn` |
| Personalnummer | `employeeID` |
| E-Mail | `mail` |
| Position | `title` |
| Telefon | `telephoneNumber` |

Zugeordnete Felder überschreibt Argus bei jeder Anmeldung. Benutzername, Vor- und Nachname kommen immer aus dem Verzeichnis. Lassen Sie eine der übrigen Zuordnungen leer, wird dieses Feld in Argus gepflegt.

### Verbindung testen

**Verbindung testen** prüft die eingegebenen, noch nicht gespeicherten Werte. Mit einem Benutzernamen zeigt Argus zusätzlich, welche Werte dieser Benutzer erhalten würde. Sein Passwort wird dabei nicht geprüft.

### Benutzer anlegen

Mit **Benutzer bei erster Anmeldung anlegen** (Standard) entsteht das Argus-Konto bei der ersten Anmeldung. Ist es aus, können sich per LDAP nur Benutzer anmelden, die es in Argus schon gibt.

## Was bei der Anmeldung passiert

1. Argus prüft zuerst lokale Konten, dann das Verzeichnis.
2. Der Filter muss genau einen Eintrag finden.
3. Argus sucht das passende Argus-Konto: zuerst über den Verzeichniseintrag, dann über den Benutzernamen (ohne Groß-/Kleinschreibung).
4. Gibt es keins, legt Argus es an. Der Benutzername wird kleingeschrieben.
5. Zugeordnete Felder werden aktualisiert.
6. Teams mit einer **LDAP-Gruppe** gleichen ihre Mitglieder ab. Verschachtelte Gruppen zählen nicht.

::: info Gut zu wissen
- Ein lokaler Administrator wird nie von einem Verzeichniskonto übernommen.
- Ein bestehendes lokales Konto mit demselben Benutzernamen wird mit dem Verzeichnis verknüpft. Hat es ein lokales Passwort, gilt dieses weiterhin.
- Das Konto muss in Argus aktiv sein.
- Ist das Verzeichnis nicht erreichbar, schlägt die Anmeldung fehl wie bei einem falschen Passwort.
:::

## Benutzer synchronisieren

**LDAP-Benutzer synchronisieren** legt Mitarbeitende vorab an oder aktualisiert sie, ohne dass sie sich anmelden müssen. So lassen sich z. B. Anforderungen für neue Kollegen erfassen, bevor sie sich zum ersten Mal anmelden.

1. Die LDAP-Anmeldung einschalten und speichern; die Synchronisierung nutzt die gespeicherte Konfiguration.
2. Einen **LDAP-Filter** eingeben oder eine Vorlage wählen: **Wie Anmeldefilter**, **Nur aktive AD-Konten** oder **Mitglied einer Gruppe**.
3. **Vorschau** zeigt pro Eintrag, ob er neu angelegt, aktualisiert, unverändert oder übersprungen wird, mit allen Änderungen.
4. Einträge auswählen und **Übernehmen**.

Die Vorschau ändert nichts. Bis zu 5000 Einträge sind möglich.

::: warning Achtung
- Die Synchronisierung läuft nur, wenn Sie sie starten. Einen Zeitplan gibt es nicht.
- Argus deaktiviert keine Konten. Wer im Verzeichnis gesperrt oder gelöscht wird, bleibt in Argus aktiv, kann sich aber nicht mehr anmelden. Deaktivieren Sie solche Konten in Argus selbst.
- Die Synchronisierung legt Konten auch dann an, wenn **Benutzer bei erster Anmeldung anlegen** aus ist.
:::
