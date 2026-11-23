# Aktivitäten

**IT-Betrieb → Aktivitäten** zeigt, wer wann was getan hat: in Anforderungen, Geräten, Verbrauchsmaterial, Lizenzen, Meldungen und Bestellungen. Die neuesten Einträge stehen oben. Das Widget **Letzte Aktivitäten** im [Dashboard](./dashboard-calendar) zeigt die letzten zehn; **Alle anzeigen** öffnet die Seite.

Jede Zeile ist ein Arbeitsschritt. Betrifft er mehrere Geräte oder Positionen, steht er trotzdem nur einmal da, mit der Anzahl:

- Die Ausgabe einer Anforderung mit drei Geräten ist eine Zeile **Ausgegeben · 3 Positionen**, mit Link zur Anforderung.
- Ein Wareneingang ist eine Zeile **Lieferung eingegangen**, auch wenn dabei Geräte angelegt und Material eingebucht werden.
- Eine Serienanlage oder ein [Import](./device-import) ist eine Zeile **Geräte angelegt** bzw. **Geräte importiert**.

Ausnahme sind die Zuweisungen beim Vorbereiten einer Anforderung: Jedes zugewiesene und jedes wieder entfernte Gerät, Material oder Lizenz ist eine eigene Zeile **Zugewiesen** bzw. **Zuweisung entfernt** mit dem Gerät, z. B. **Zugewiesen · NB-0012 · ThinkPad T14**. Hat **Automatisch zuweisen** oder ein Wareneingang zugewiesen, steht das in Klammern dahinter.

## Spalten

| Spalte | Inhalt |
| --- | --- |
| **Zeitpunkt** | Wann der Schritt erfasst wurde |
| **Bereich** | Anforderungen, Geräte, Verbrauchsmaterial, Lizenzen, Meldungen oder Bestellungen |
| **Objekt** | Die Anforderung, das Gerät, die Lizenz usw.; ein Klick öffnet es |
| **Aktivität** | Was getan wurde, ggf. mit Anzahl |
| **Bearbeiter** | Wer es getan hat |
| **Mitarbeiter** | Wen es betrifft, z. B. den Anforderer |
| **Detail** | Kommentar oder Beschreibung; über **Spalten** einblendbar |

Filtern lässt sich nach **Bereich**, **Aktivität**, **Bearbeiter** und **Zeitpunkt**, die Suche findet Objekte, Details und Namen.

## Detailverlauf einer Anforderung {#detailverlauf}

**Detailverlauf** in der Karte **Verlauf** einer [Anforderung](./requests#verlauf) öffnet diese Seite nur mit den Einträgen dieser Anforderung. Dort steht jeder Schritt, auch jede einzelne Zuweisung und Entfernung mit Person und Uhrzeit. **Alle anzeigen** hebt die Einschränkung auf.

::: info Gut zu wissen
- Sie sehen nur Einträge aus Bereichen, die Sie lesen dürfen.
- Gelöschte Geräte, Lizenzen und Bestellungen bleiben mit ihrem Namen in der Liste, aber ohne Link.
- Änderungen an Stammdaten, Benutzern, Rollen und Einstellungen erscheinen hier nicht.
- Einzelne Zuweisungen werden erst seit dieser Version erfasst. Bei älteren Anforderungen steht nur der Abschluss der Vorbereitung.
- Einträge von vor der Einführung der Seite wurden aus der vorhandenen Historie übernommen: Anforderungen, Servicebuch, Lagerbewegungen und Meldungen. Von Bestellungen ist nur das Anlegen bekannt, von Lizenzen nichts.
- Das [Servicebuch](./devices#servicebuch) eines Geräts bleibt unverändert: Dort steht jede Ausgabe weiterhin beim einzelnen Gerät.
:::
