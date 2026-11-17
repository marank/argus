# FAQ

Fragen von Mitarbeitenden stehen in der [FAQ für Mitarbeitende](../employees/faq).

## Für die IT

### Warum erscheint eine Anforderung nicht bei mir?

- Sie wartet noch auf die Genehmigung (**In Genehmigung**).
- Die Ansicht ist gefiltert, z. B. auf **Nur offene** oder ein Team.
- Ihnen fehlt das Recht auf **Anforderungen & Kalender**.

### Warum lässt sich ein Gerät nicht zuweisen?

Es ist nicht **Im Lager**, gehört zu einem anderen Modell als die Position oder ist nicht **Verleihbar (Pool)**. Die Fehlermeldung nennt den Grund.

### Eine Anforderung kam ohne Genehmigung, obwohl die Kategorie genehmigungspflichtig ist.

Mögliche Gründe:

- Der Mitarbeiter ist von Genehmigungen befreit.
- Die IT hat die Anforderung in seinem Namen erfasst.
- Der Mitarbeiter ist selbst Genehmiger seiner Abteilung.
- Weder seine Abteilung noch eine übergeordnete hat Genehmiger.

### Das Gerät ist schon beim Mitarbeiter, aber die Anforderung noch offen.

**Als ausgegeben markieren** auf der bestätigten Anforderung. Die Geräte erfassen Sie später. Siehe [Ohne erfasste Geräte ausgeben](./requests#ohne-erfasste-gerate-ausgeben).

### Ein Gerät wurde gestohlen.

Den Status auf **Verloren** setzen. Eine Meldung „Verloren oder gestohlen“ tut das nicht automatisch. Braucht der Mitarbeiter Ersatz, nutzen Sie **Ersetzen** auf dem gestohlenen Gerät; der Gerätename geht auf das Ersatzgerät über.

### Warum bekommt ein neues Gerät die Nummer INV-… statt der Kategorie-Nummer?

Die Nummernserie ist an einer übergeordneten Kategorie hinterlegt. Serien werden nicht vererbt. Hinterlegen Sie die Serie an der Unterkategorie oder am Modell.

### Kann ich eine Rückgabe-Erinnerung sofort schicken?

Ja, mit **An Rückgabe erinnern** auf der Anforderung oder im Dashboard-Widget **Überfällige Rückgaben**.

### Wie exportiere ich die Geräteliste?

Einen Export gibt es derzeit nicht.

### Ein gerade gescanntes Gerät wurde nicht gefunden.

Ist der Cursor in einem Eingabefeld, landet der Scan dort. Klicken Sie außerhalb oder scannen Sie direkt ins Feld **Scannen**.

## Für Administratoren

### Ein neu angelegter Benutzer kann sich nicht anmelden.

In Argus angelegte Benutzer haben zunächst kein Passwort. Sie melden sich per LDAP an, oder Sie setzen unter **Stammdaten → Mitarbeiter** mit **Passwort setzen** eines.

### Ein Mitarbeiter hat das Unternehmen verlassen.

Geräte zurücknehmen, Lizenzen entfernen und das Konto deaktivieren. Löschen lässt es sich nicht, solange es Anforderungen gibt; die Historie bleibt so erhalten. Argus deaktiviert Konten nicht automatisch, auch nicht über LDAP.

### Ein IT-Mitarbeiter sieht keine IT-Bereiche.

Ihm fehlt eine Rolle. Rollen vergibt nur ein Administrator unter **Stammdaten → Rollen** oder beim Mitarbeiter.

### E-Mails kommen nicht an.

Siehe [Updates und Fehlersuche](./operations/maintenance#e-mails-kommen-nicht-an).

### Kann ich ein Modul abschalten, ohne Daten zu verlieren?

Ja. Abgeschaltete Module verschwinden aus der Oberfläche; die Daten bleiben erhalten.

### Wo ändere ich mein Passwort?

Lokale Konten im Benutzermenü unter **Anmeldung & Sicherheit → Passwort ändern**, LDAP-Konten im Verzeichnis. Siehe [Passwörter lokaler Konten](./administration/sign-in#passworter-lokaler-konten).
