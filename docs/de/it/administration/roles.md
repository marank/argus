# Rollen und Rechte

Argus unterscheidet vier Arten von Benutzern. Für IT-Mitarbeitende steuern Rollen, welche Bereiche sie sehen und ändern.

## Benutzerarten

| Art | Kennzeichen | Sieht |
| --- | --- | --- |
| **Mitarbeiter** | – | Dashboard, Self-Service und das eigene Profil |
| **IT-Mitarbeiter** | **IT-Mitarbeiter** | Zusätzlich die IT-Bereiche, je nach Rollen |
| **Administrator** | **Administrator** | Alles, inklusive Rollen und Einstellungen |
| **Abholterminal** | **Abholterminal** | Nur das [Abholterminal](../terminal) |

**Genehmiger** ist keine eigene Art: Wer an einer Abteilung als Genehmiger eingetragen ist, sieht zusätzlich **Genehmigungen**.

Die Kennzeichen setzen Sie unter **Stammdaten → Mitarbeiter**. Nur Administratoren ernennen Administratoren.

## Rollen

Rollen legt ein Administrator unter **Stammdaten → Rollen** an. Jede Rolle hat Mitglieder und für jeden Bereich eine Stufe:

| Stufe | Wirkung |
| --- | --- |
| **Kein Zugriff** | Der Bereich ist ausgeblendet. |
| **Lesen** | Der Bereich ist sichtbar, ohne Änderungsmöglichkeit. |
| **Schreiben** | Ansehen und ändern |

### Bereiche

**Stammdaten:** Modelle, Kategorien (inklusive Komponenten), Hersteller, Lieferanten, Standorte, Abteilungen, Teams, Mitarbeiter, Nummernserien

**IT-Betrieb:** Anforderungen & Kalender, Geräte & Servicebuch, Verbrauchsmaterial, Lizenzen, Meldungen, Beschaffung

### Wie Rechte zusammenwirken

- Ein Benutzer kann mehrere Rollen haben. Pro Bereich gilt die höchste Stufe aus allen Rollen.
- Rollen wirken nur bei **IT-Mitarbeitern**. Ein Mitarbeiter ohne dieses Kennzeichen hat trotz Rolle keine IT-Rechte.
- Administratoren haben immer alle Rechte, unabhängig von Rollen.
- Ein neuer IT-Mitarbeiter ohne Rolle sieht noch keine IT-Bereiche.
- Auswahllisten in Formularen funktionieren auch ohne Recht auf den Bereich. Wer Anforderungen bearbeitet, kann z. B. Standorte auswählen, ohne die Standortverwaltung zu sehen.

::: tip Tipp
Bewährt haben sich wenige, klar geschnittene Rollen, z. B. „Service Desk“ (Anforderungen, Geräte, Meldungen schreiben; Stammdaten lesen) und „Einkauf“ (Beschaffung, Lieferanten schreiben).
:::

## Was nur Administratoren dürfen

- Rollen anlegen und vergeben
- Administratoren ernennen, ändern, löschen und deren Zwei-Faktor-Anmeldung zurücksetzen
- Alles unter **Administration → Einstellungen**

Ein Administrator kann sich weder selbst deaktivieren noch sich die Administratorrechte entziehen.

::: info Gut zu wissen
- Wer **Mitarbeiter** schreiben darf, kann andere zu IT-Mitarbeitern oder Terminal-Konten machen. Rechte erhalten diese erst durch eine Rolle, die nur ein Administrator vergibt.
- Benachrichtigungen an „die IT“ gehen an alle IT-Mitarbeiter, unabhängig von ihren Rollen, sofern kein Team zuständig ist. Ein Administrator ohne das Kennzeichen **IT-Mitarbeiter** erhält sie nicht.
- Der erste Administrator aus der Installation erhält bei jedem Neustart wieder Administratorrechte.
:::
