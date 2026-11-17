# Erste Schritte für Administratoren

Von der frisch installierten Instanz zum Echtbetrieb. Die Installation selbst beschreibt [Installation](../operations/installation).

## Checkliste

### 1. Grundeinstellungen

- Mit dem ersten Administrator anmelden und eine [Zwei-Faktor-Anmeldung](./sign-in#zwei-faktor-anmeldung) einrichten.
- Unter **Einstellungen → Module & Funktionen** abschalten, was nicht gebraucht wird.
- Unter **Einstellungen → Fristen & Vorwarnzeiten** Ausleihdauer und Erinnerungen festlegen.

### 2. E-Mail

- Unter **Einstellungen → E-Mail** den SMTP-Server eintragen, **App-Adresse** setzen, **E-Mails senden** einschalten.
- Testmail senden.
- Unter **Einstellungen → Benachrichtigungen** prüfen, welche Benachrichtigungen es geben soll.

Siehe [E-Mail und Benachrichtigungen](./email).

### 3. Anmeldung

- LDAP einrichten und mit **Verbindung testen** prüfen, siehe [LDAP-Anmeldung](./ldap).
- Mitarbeitende mit **LDAP-Benutzer synchronisieren** vorab anlegen.

### 4. Stammdaten

- Nummernserien für Inventarnummern und ggf. Gerätenamen anlegen.
- Standorte mit Lagern und Abholorten anlegen.
- Abteilungen mit Genehmigern anlegen.
- IT-Teams anlegen, ein Standard-Team festlegen.
- Hersteller und Lieferanten anlegen.
- Kategorien mit Nummernserie, Team, Portal-Einstellungen und Genehmigungspflicht anlegen.
- Modelle anlegen.

Siehe [Stammdaten](./master-data).

### 5. IT-Team

- Rollen anlegen, siehe [Rollen und Rechte](./roles).
- IT-Mitarbeitende als **IT-Mitarbeiter** kennzeichnen und ihnen Rollen und Teams geben.

### 6. Bestand

- Geräte importieren, siehe [Geräte importieren](../device-import).
- Verbrauchsmaterial mit Mindestbeständen anlegen und einbuchen.
- Lizenzen erfassen und zuweisen.

### 7. Abholterminal

- Terminal-Konto anlegen, Passwort setzen, am Touch-PC anmelden. Siehe [Abholung am Terminal](../terminal#einrichtung).

### 8. Betrieb

- TLS-Proxy und `TRUSTED_PROXIES` prüfen.
- Sicherungen außer Haus kopieren und eine Wiederherstellung testen, siehe [Backups](../operations/backups).

## Danach

- Mitarbeitende auf [Erste Schritte für Mitarbeitende](../../employees/getting-started) hinweisen.
- Die IT auf [Erste Schritte für die IT](../getting-started) hinweisen.
