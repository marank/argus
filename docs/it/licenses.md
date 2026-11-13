# Lizenzen

Unter **IT-Betrieb → Lizenzen** verwalten Sie Softwarelizenzen mit Plätzen, Laufzeit und Zuweisungen.

## Lizenz anlegen

Voraussetzung ist ein Modell mit der Führung **Softwarelizenz** in einer Software-Kategorie, z. B. „Microsoft 365 E3“.

| Feld | Bedeutung |
| --- | --- |
| **Software** | Das Modell |
| **Vertrag / Referenz** | Unterscheidet mehrere Lizenzen derselben Software, z. B. die Vertragsnummer |
| **Lizenzschlüssel** | Optional |
| **Plätze** | Wie viele Zuweisungen möglich sind |
| **Zuweisung an** | **Mitarbeiter** (z. B. Microsoft 365) oder **Geräte** (z. B. Windows, Virenschutz) |
| **Gültig ab**, **Gültig bis** | Leer bei „Gültig bis“ heißt unbefristet |
| **Lieferant**, **Kaufdatum**, **Kaufpreis**, **Notizen** | Kaufdaten |

Die Liste zeigt die belegten Plätze und markiert Lizenzen als **läuft bald ab** oder **abgelaufen**.

## Zuweisen

Auf der Lizenzseite wählen Sie unter **Zuweisungen** einen Mitarbeiter oder ein Gerät, optional mit Hinweis, und klicken **Hinzufügen**. Mit **Zuweisung entfernen** geben Sie einen Platz wieder frei.

Abgelaufene Lizenzen und Lizenzen ohne freie Plätze lassen sich nicht zuweisen.

Mitarbeitende sehen ihre Lizenzen im Self-Service unter **Meine Software**, ohne Lizenzschlüssel.

## Software über Anforderungen

Mitarbeitende fordern Software im Self-Service an, sofern **Software anfordern** in den Einstellungen eingeschaltet ist. Bei der Bearbeitung wählt die IT eine Lizenz mit freiem Platz, siehe [Anforderungen bearbeiten](./requests#software).

Wird eine Zuweisung entfernt, die über eine Anforderung kam, gilt sie dort als zurückgegeben.

## Ablauf und Warnungen

Endet eine befristete Lizenz innerhalb der Vorwarnzeit (Standard: 60 Tage), erscheint sie:

- auf dem Dashboard unter **Lizenzende ≤ {n} Tage**
- im Kalender als **Lizenz endet**
- als Benachrichtigung **Lizenz läuft ab** an die IT, einmal pro Lizenz und Enddatum

Verlängern Sie eine Lizenz durch ein neues **Gültig bis**, warnt Argus vor dem neuen Ende erneut.

## Ändern und löschen

- Plätze lassen sich nicht unter die Zahl der belegten Plätze senken.
- **Zuweisung an** lässt sich nur ändern, wenn keine Zuweisungen bestehen.
- Eine Lizenz lässt sich nur löschen, wenn keine Zuweisungen bestehen.

::: info Gut zu wissen
Bestellte Lizenzen legt der Wareneingang nicht automatisch an. Erfassen Sie sie nach der Lieferung hier.
:::
