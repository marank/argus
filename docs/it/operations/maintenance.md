# Updates und Fehlersuche

## Auf eine neue Version aktualisieren

1. Vorher sichern:

   ```bash
   docker compose exec app python manage.py backup_database
   ```

2. Neue Version starten, je nach [Installationsweg](./installation):

   **Mit fertigem Image:** Mit einem Tag wie `:1` holt `pull` die neueste passende Version. Für einen Versionssprung tragen Sie vorher den neuen Tag in `ARGUS_IMAGE` ein.

   ```bash
   docker compose pull app
   ```

   ```bash
   docker compose up -d
   ```

   **Aus dem Repository:**

   ```bash
   git pull
   ```

   ```bash
   docker build -t argus:latest .
   ```

   ```bash
   docker compose up -d
   ```


Beim Start spielt Argus die Datenbankmigrationen automatisch ein. Während des Neustarts ist Argus einige Sekunden nicht erreichbar.

## Zustand prüfen

| Prüfung | Befehl |
| --- | --- |
| Laufen alle Dienste? | `docker compose ps` |
| Ist Argus erreichbar? | `curl -fsS http://localhost:8080/api/health` |
| Protokoll ansehen | `docker compose logs -f app` |

`/api/health` ist ohne Anmeldung erreichbar und dient auch Docker als Health-Check. Der Status `healthy` in `docker compose ps` bedeutet, dass Weboberfläche und API antworten.

Im `app`-Container laufen mehrere Prozesse: nginx, die Anwendung, ein Prozess für Live-Updates und ein Worker für Hintergrundjobs (E-Mails, Erinnerungen). Fällt einer davon wiederholt aus, beendet sich der Container. Docker startet ihn dann neu, und die Ursache steht im Protokoll.

## Passwort zurücksetzen

Im Normalfall setzt ein Administrator das Passwort direkt in Argus, siehe [Passwörter lokaler Konten](../administration/sign-in#passworter-lokaler-konten).

Auf der Kommandozeile geht das auch ohne Anmeldung, z. B. wenn sich kein Administrator mehr anmelden kann:

```bash
docker compose exec app python manage.py set_password admin
```

Der Befehl fragt das neue Passwort zweimal ab und hebt eine Sperre nach Fehlversuchen für dieses Konto auf. Mit `--reset-two-factor` schaltet er zusätzlich die Zwei-Faktor-Anmeldung des Benutzers ab.

Anders als in Argus prüft der Befehl die Passwortregeln nicht. LDAP-Benutzer ändern ihr Passwort im Verzeichnis.

::: warning Achtung
Setzen Sie für einen LDAP-Benutzer kein lokales Passwort. Argus prüft das lokale Passwort zuerst; es würde neben dem Verzeichnispasswort gelten.
:::

## Wartungsbefehle

Alle Befehle laufen im `app`-Container: `docker compose exec app python manage.py <Befehl>`.

| Befehl | Zweck |
| --- | --- |
| `set_password <benutzer>` | Neues Passwort setzen, Sperre aufheben. Optionen: `--password`, `--reset-two-factor` |
| `send_reminders` | Fällige Rückgabe- und Lizenzerinnerungen sofort verschicken. Der Worker erledigt das ohnehin stündlich. |
| `seed_demo` | Demodaten anlegen, nur für Testinstanzen |
| `createsuperuser` | Weiteren lokalen Administrator anlegen |

## Hintergrundjobs

E-Mails und Erinnerungen laufen über eine Warteschlange in der Datenbank. Kann der Mailserver eine Nachricht nicht annehmen, versucht Argus es etwa einen Tag lang erneut. Wartende, fehlgeschlagene und erledigte Jobs zeigt der Django-Admin unter `/admin/` (nur Administratoren).

Erinnerungen (Rückgaben, Lizenzabläufe) verschickt der Worker stündlich. Erledigte Jobs löscht er nach 24 Stunden, fehlgeschlagene nach 14 Tagen. Gelesene Benachrichtigungen in der App verschwinden nach 90 Tagen.

Wird der E-Mail-Versand abgeschaltet, verschickt Argus auch bereits wartende Mails nicht mehr.

## Häufige Probleme

### Die Anmeldung schlägt sofort fehl oder die Seite meldet einen CSRF-Fehler

Die aufgerufene Adresse fehlt in `APP_URLS`, oder Argus läuft hinter einem TLS-Proxy, dessen Adresse nicht in `TRUSTED_PROXIES` steht. Siehe [Hinter einem TLS-Proxy](./installation#hinter-einem-tls-proxy).

### Der Container startet nicht

Häufigste Ursachen im Protokoll (`docker compose logs app`):

- `SECRET_KEY` fehlt, ist kürzer als 40 Zeichen oder ein Platzhalter wie `change-me`.
- Die Datenbank ist nicht erreichbar: `POSTGRES_PASSWORD` stimmt nicht mit dem Passwort überein, mit dem das Datenbank-Volume angelegt wurde.

### Änderungen anderer erscheinen erst nach dem Neuladen

Der Proxy puffert die Live-Updates. Schalten Sie für `/api/events` das Puffern ab, siehe [Live-Updates durch den Proxy](./installation#live-updates-durch-den-proxy).

### Ab mehreren offenen Tabs lädt Argus nicht mehr

Argus wird direkt über HTTP aufgerufen, ohne HTTP/2-fähigen Proxy. Browser erlauben dann nur sechs Verbindungen pro Adresse. Lösung: TLS-Proxy mit HTTP/2 davor setzen.

### E-Mails kommen nicht an

1. Unter **Einstellungen → E-Mail** prüfen, ob **E-Mails senden** eingeschaltet ist, und eine Testmail senden. Die Testmail geht auch bei abgeschaltetem Versand raus. Kommt sie an, normale Mails aber nicht, liegt es meist an diesem Schalter.
2. Im Django-Admin die fehlgeschlagenen Jobs und deren Fehlermeldung prüfen.
3. Prüfen, ob die Benachrichtigungsart unter **Einstellungen → Benachrichtigungen** eingeschaltet ist und der Empfänger sie nicht abbestellt hat.
4. Prüfen, ob der Empfänger eine E-Mail-Adresse hat.

### Ein neu angelegter Benutzer kann sich nicht anmelden

In Argus angelegte Benutzer haben zunächst kein Passwort. Sie melden sich per LDAP an, oder ein Administrator setzt unter **Stammdaten → Mitarbeiter** mit **Passwort setzen** eines.

### Das Abholterminal ist abgemeldet

Die Anmeldung ist abgelaufen, standardmäßig nach 12 Stunden. Tragen Sie am Terminal-Konto eine längere **Sitzungsdauer (Stunden)** ein, siehe [Anmeldung und Sicherheit](../administration/sign-in#anmelden).
