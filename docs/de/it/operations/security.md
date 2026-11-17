# Sicherheit

Ein Überblick darüber, wie Argus abgesichert ist und was der Betrieb dazu beiträgt.

## Container

- Der `app`-Container läuft als unprivilegierter Benutzer, ohne Linux-Capabilities und mit schreibgeschütztem Dateisystem. Beschreibbar ist nur `/tmp` im Arbeitsspeicher.
- `no-new-privileges` verhindert Rechteausweitung über setuid-Programme.
- Code und Konfiguration im Image gehören `root`; die Anwendung kann sie lesen, aber nicht ändern.
- Die nächtliche Sicherung läuft im `app`-Container. Die Sicherungsdateien kann nur dessen Benutzer lesen, denn sie enthalten Passwort-Hashes und personenbezogene Daten.

## Im Browser

- Anmeldung über Sitzungs-Cookies mit CSRF-Schutz. Eine Anmeldung gilt standardmäßig 12 Stunden; einstellbar für alle und pro Konto. Die Cookies sind als `Secure` markiert, wenn alle Adressen in `APP_URLS` HTTPS verwenden.
- Eine Content Security Policy erlaubt Skripte, Schriften und Verbindungen nur von Argus selbst. Argus lädt nichts von fremden Servern.
- Argus darf nur von sich selbst eingebettet werden (Schutz gegen Clickjacking).

## Anmeldung

- Passwörter werden mit Argon2 gespeichert.
- Nach Fehlversuchen sperrt Argus weitere Anmeldungen für 15 Minuten: bei 10 falschen Passwörtern für einen Benutzernamen, bei 30 von einer Adresse und bei 10 falschen Codes im zweiten Schritt. Damit die Sperre pro Client und nicht pro Proxy greift, muss `TRUSTED_PROXIES` gesetzt sein.
- Jeder Benutzer kann eine [Zwei-Faktor-Anmeldung](../administration/sign-in) einrichten.
- Der Django-Admin unter `/admin/` nutzt dieselbe Anmeldung, inklusive zweitem Faktor.

## Was der Betrieb beitragen muss

- Argus nur über HTTPS bereitstellen; HSTS am Proxy setzen.
- `SECRET_KEY` und `.env` geheim halten. Wer den `SECRET_KEY` kennt, kann Sitzungen fälschen.
- Sicherungen außerhalb des Servers verwahren und vor fremdem Zugriff schützen. Sie enthalten auch die Passwörter für SMTP und das LDAP-Dienstkonto, sofern diese in Argus und nicht per Umgebungsvariable hinterlegt sind.
- Neue Versionen zeitnah einspielen. Das Image wird beim Bauen auf bekannte Schwachstellen geprüft.
