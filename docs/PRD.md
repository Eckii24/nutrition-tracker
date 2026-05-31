# PRD: AI-Powered Nutrition Tracker

## 1. Kurzfassung

Wir bauen einen persönlichen Nutrition Tracker, der Mahlzeiten über **Bild + Freitext** oder **nur Freitext** erfasst, die Nährwerte **tagesscharf** aggregiert und gegen definierte Ziele auswertet.

**Empfehlung:** dateibasiert als Standard, *nicht* SQLite-first.

**Warum:**
- leicht nachvollziehbar und git-freundlich
- einfache manuelle Korrekturen
- transparent für Review/Audit
- gut passend zu einem persönlichen, agent-gestützten Workflow

**Einschränkung:** Rohbilder gehören **nicht** in Git. Strukturierte Daten ja, große Binärdaten nein.

---

## 2. Problem

Heute ist Ernährungstracking oft entweder:
- zu manuell
- zu app-zentriert und intransparent
- schlecht auditierbar
- schwach integrierbar in AI-Workflows

Gesucht ist ein System, das:
- mit Fotos und knappen Beschreibungen funktioniert
- Tagesziele für Makros, Mikros und Kalorien verfolgt
- Unschärfe explizit behandelt
- qualitative Ernährungsbewertung liefert
- lokal/dateibasiert bleibt, soweit sinnvoll

---

## 3. Produktziel

Der Nutzer schickt dem System im Alltag Fotos oder Beschreibungen seiner Mahlzeiten.
Das System soll daraus:
1. Mahlzeiten erkennen bzw. schätzen
2. Nährwerte pro Mahlzeit erfassen
3. Tageswerte aggregieren
4. Zielerreichung bewerten
5. qualitative Hinweise geben
6. Korrekturen und Unsicherheit sauber behandeln

---

## 4. Nicht-Ziele

Vorerst **nicht** im Scope:
- Barcode-Scanning
- vollständige medizinische Diagnostik
- vollautomatische Mikronährstoff-Perfektion ohne Nutzerkorrektur
- Multi-User / Social Features
- native Mobile-App als erstes Artefakt
- perfektes Gewichtsmanagement-/Coachingsystem

---

## 5. Nutzer-Workflow

### Primärer Flow
1. Nutzer sendet Bild einer Mahlzeit oder beschreibt sie in Text.
2. System extrahiert Lebensmittel, Mengen und Zubereitungsart.
3. System schätzt Nährwerte mit Konfidenz/Unsicherheit.
4. System speichert einen strukturierten Mahlzeiteneintrag.
5. System aktualisiert den Tagessaldo.
6. System antwortet mit:
   - erkannte Mahlzeit
   - geschätzte Kalorien
   - Makros
   - relevante Mikros
   - Fortschritt gegen Tagesziele
   - kurze qualitative Bewertung

### Korrektur-Flow
1. Nutzer korrigiert Bestandteile oder Mengen.
2. System erstellt keine stille Überschreibung, sondern eine nachvollziehbare Korrektur.
3. Tagessummen werden neu berechnet.

### Tages-Review-Flow
Nutzer fragt z. B.:
- "Was fehlt mir heute noch?"
- "Habe ich mein Eiweißziel erreicht?"
- "Wie gut habe ich mich heute ernährt?"

System liefert:
- aktueller Tagesstand
- Differenz zu Zielen
- knappe qualitative Einordnung
- ggf. konkrete Lücken, z. B. Protein, Ballaststoffe, Kalium

---

## 6. Funktionsanforderungen

### 6.1 Eingaben
Das System muss unterstützen:
- Bild einer Mahlzeit
- Freitextbeschreibung einer Mahlzeit
- Bild + Freitext zusammen
- manuelle Korrektur bestehender Einträge
- explizite Zieldefinitionen

### 6.2 Tracking
Das System muss pro Mahlzeit mindestens speichern:
- Zeitpunkt
- Quelle (`image`, `text`, `image+text`, `manual`)
- erkannte Lebensmittel
- geschätzte Mengen
- Kalorien
- Makros:
  - Protein
  - Fett
  - Kohlenhydrate
  - optional Ballaststoffe separat
- Mikronährstoffe (erste Priorität konfigurierbar)
- Unsicherheits-/Konfidenz-Hinweis
- Freitextnotizen
- Korrekturhistorie

### 6.3 Ziele
Das System muss Ziele unterstützen für:
- Kalorien
- Protein
- Fett
- Kohlenhydrate
- Ballaststoffe
- ausgewählte Mikronährstoffe

Zieltypen:
- Mindestziel
- Maximalziel
- Zielbereich

### 6.4 Auswertung
Das System muss berechnen:
- Tagessummen
- Rest bis Ziel
- Über-/Unterschreitung
- Anteil der Zielerreichung in Prozent
- Qualitätsheuristik für den bisherigen Tag

### 6.5 Qualitative Bewertung
Das System soll nicht nur Zahlen liefern, sondern bewerten:
- Protein ausreichend / knapp / deutlich zu niedrig
- Energiebalance grob passend / fraglich / deutlich daneben
- Verteilung stark ultraverarbeitet vs. eher vollwertig
- Mikronährstoffabdeckung plausibel / lückenhaft / unbekannt
- Gemüse-/Obst-/Ballaststoffsignal

Wichtig: Diese Bewertung ist **heuristisch**, nicht medizinisch belastbar.

---

## 7. Qualitätsanforderungen

### 7.1 Nachvollziehbarkeit
Jede Zahl muss auf einen nachvollziehbaren Eintrag zurückführbar sein.

### 7.2 Korrigierbarkeit
Manuelle Korrekturen müssen einfach sein.

### 7.3 Unsicherheitsbehandlung
Das System darf bei Bildern keine Scheingenauigkeit vortäuschen.
Wenn Mengen oder Zutaten unsicher sind, muss das erkennbar sein.

### 7.4 Git-Freundlichkeit
Die Kern-Datenhaltung soll diffbar sein.

### 7.5 Lokale Robustheit
Das System soll ohne Cloud-Datenbank funktionieren.

---

## 8. Architekturentscheidung: dateibasiert vs. SQLite

## Empfehlung
**Start dateibasiert.**

## Begründung
Für den geschilderten Use Case ist eine dateibasierte Architektur zunächst die bessere Default-Entscheidung:
- einzelne Mahlzeiten sind natürliche Dokumente/Ereignisse
- Tagesaggregate lassen sich deterministisch neu berechnen
- Git-Diffs sind nützlich für Korrekturen
- Export/Backup ist trivial
- geringe Komplexität in der frühen Produktphase

## Gegenargumente gegen strikt dateibasiert
Dateibasiert wird schwächer bei:
- komplexen Ad-hoc-Abfragen über lange Zeiträume
- performanter Statistik über Monate/Jahre
- konkurrierenden Schreibzugriffen
- starkem Schema-Wandel ohne Migrationsdisziplin

## Pragmatische Entscheidung
**Phase 1:** append-only dateibasiert

**Phase 2 optional:** SQLite-Read-Model oder Cache für schnellere Analysen

Das ist die saubere Trennung:
- **Source of Truth:** Dateien
- **abgeleitete Indizes/Aggregate:** optional SQLite

Das ist robuster als SQLite-first, wenn Transparenz und Git-Tracking wichtig sind.

---

## 9. Vorgeschlagenes Datenmodell

## 9.1 Source of Truth
Empfehlung: **JSON pro Event / JSONL pro Tag** statt freie Markdown-Daten.

Grund:
- maschinenfreundlich
- validierbar
- diffbar
- leichter deterministisch zu verarbeiten

Markdown kann zusätzlich für menschenlesbare Reports erzeugt werden, sollte aber nicht das Primärformat für strukturierte Nährwerte sein.

## 9.2 Verzeichnisstruktur

```text
nutrition-tracker/
  docs/
    PRD.md
  data/
    profile/
      user.json
      goals.json
      nutrition_targets.json
    meals/
      2026/
        2026-05-31.jsonl
    corrections/
      2026/
        2026-05-31.jsonl
    daily/
      2026/
        2026-05-31.summary.json
        2026-05-31.report.md
  schemas/
    meal-entry.schema.json
    correction-entry.schema.json
    daily-summary.schema.json
```

## 9.3 Meal Entry Beispiel

```json
{
  "id": "meal_2026-05-31T12-34-56_001",
  "timestamp": "2026-05-31T12:34:56+02:00",
  "source": "image+text",
  "input_refs": {
    "telegram_message_id": "optional",
    "image_path": "optional/local/path/or-hash"
  },
  "foods": [
    {
      "label": "Hähnchenbrust",
      "amount": 180,
      "unit": "g",
      "estimated": true
    },
    {
      "label": "Reis gekocht",
      "amount": 220,
      "unit": "g",
      "estimated": true
    }
  ],
  "nutrition": {
    "kcal": 620,
    "protein_g": 48,
    "fat_g": 14,
    "carbs_g": 71,
    "fiber_g": 4
  },
  "micros": {
    "potassium_mg": 780,
    "magnesium_mg": 95,
    "vitamin_c_mg": 12
  },
  "confidence": "medium",
  "assumptions": [
    "Reis als gekocht angenommen",
    "Kein zusätzliches Öl sichtbar"
  ],
  "notes": "Mittagessen nach Training"
}
```

## 9.4 Korrekturmodell

Keine destruktive Mutation als erste Wahl.
Stattdessen Korrektur-Event, z. B.:
- Menge angepasst
- Zutat ergänzt
- Mahlzeit gelöscht / storniert

So bleibt Historie erhalten.

---

## 10. Bewertungslogik

## 10.1 Quantitativ
Für jeden Tag berechnen:
- absolute Summen
- Differenz zu Ziel
- Prozent Zielerreichung
- Bereichsverletzungen

## 10.2 Qualitativ
Heuristische Bewertung entlang mehrerer Achsen:
- Proteinabdeckung
- Kalorienziel grob getroffen?
- Ballaststoffabdeckung
- Obst-/Gemüseindikatoren
- Verarbeitungsgrad grob
- Mikronährstofflücken mit hoher Plausibilität

## 10.3 Unsicherheit
Bewertungen sollen Unsicherheit berücksichtigen.
Beispiel:
- "Eiweißziel wahrscheinlich erreicht"
- statt: "Eiweißziel erreicht"

Wenn Datenlage schwach ist, muss das Ergebnis defensiver formuliert werden.

---

## 11. AI-Rolle im System

AI soll verwendet werden für:
- Bilderkennung/Interpretation
- Extraktion aus Freitext
- Schätzung fehlender Mengen
- qualitative Tagesbewertung
- Rückfragen bei Unklarheit

AI soll **nicht** unkontrolliert Source-of-Truth-Daten frei erfinden.
Deshalb braucht es:
- strukturierte Extraktion
- Schema-Validierung
- explizite Annahmen
- Korrekturmechanismus

---

## 12. Risiken

### Risiko 1: Scheingenauigkeit
Ein Foto erlaubt oft nur grobe Schätzungen.

**Gegenmaßnahme:** Konfidenz und Annahmen pro Eintrag speichern.

### Risiko 2: Mikronährstoffe sind lückenhaft
Ohne verlässliche Produkt-/Rezeptdaten sind Mikros oft nur grob abschätzbar.

**Gegenmaßnahme:** Mikros als „best effort“ behandeln und priorisierte Kernmikros definieren.

### Risiko 3: Bilder in Git sind Mist
Repos mit Binärdaten werden schnell unhandlich.

**Gegenmaßnahme:** Bilder nur referenzieren oder separat cachen; strukturierte Extrakte versionieren.

### Risiko 4: freie Texteingaben sind uneinheitlich
"Eine Schüssel Pasta" ist ohne Nachfragen schwach.

**Gegenmaßnahme:** Rückfragen oder konservative Defaults mit offener Unsicherheitsmarkierung.

---

## 13. Erfolgskriterien

Das Produkt ist nützlich, wenn es zuverlässig ermöglicht:
- Mahlzeiten in unter 30 Sekunden zu erfassen
- Tagesstand jederzeit abzufragen
- Protein/Kalorien-Ziele sinnvoll zu verfolgen
- grobe Ernährungsqualität einschätzen zu lassen
- Einträge später leicht zu korrigieren

---

## 14. MVP-Vorschlag

### MVP Scope
- lokale dateibasierte Speicherung als Source of Truth
- primärer Hermes-/Telegram-Workflow
- lokale CLI als internes Werkzeug für manuelle Erfassung, Korrektur und Auswertung
- Mahlzeitserfassung per Text
- Mahlzeitserfassung per Bild + kurze Beschreibung
- Tagesaggregation
- Wochenmittel auf Basis aggregierter Tageswerte
- Ziele für Kalorien + Makros + Ballaststoffe
- Zielableitung aus Profilwerten in `settings.json`, aber überschreibbar
- analytisch-coachende qualitative Tagesbewertung im LLM-Layer
- manuelle Korrektur von Mahlzeiten per natürlicher Sprache

### Nicht im MVP
- native Web-UI
- umfangreiche Monatsanalytics über Standard-Weekly-Averages hinaus
- tiefe Rezeptverwaltung
- Barcode-Scanner
- persistente Bildspeicherung
- externe Food-DB-Integrationen mit großem Scope
- vollautomatische Mikronährstoffabdeckung für jedes Lebensmittel

---

## 15. Festgezurrte Produktentscheidungen

1. **Plattformform**
   - primär Hermes-/Telegram-Workflow
   - zusätzlich lokale CLI als internes Werkzeug ohne eigenen LLM-Bezug
   - die CLI liefert strukturierte Rohdaten; Coaching passiert im Skill/LLM-Layer

2. **Zielmodell**
   - Tagesziele + Wochenmittel
   - keine separaten Trainings-/Ruhetag-Ziele im MVP
   - Ziele werden aus Profilwerten abgeleitet und können manuell überschrieben werden

3. **Mikronährstoffe**
   - im MVP keine priorisierte Mikro-Zielsteuerung
   - Mikros bleiben optionales Beifang-Signal, aber nicht zentraler Scope

4. **Bewertungslogik**
   - analytisch und coachend
   - CLI selbst bewertet nicht frei-textlich; sie liefert Fakten/Signals
   - der Skill formuliert die eigentliche Ernährungsbewertung

5. **Korrektur-UX**
   - primär natürlicher Sprachstil
   - stabile IDs existieren intern trotzdem für Referenz und Revisionssicherheit

6. **Bilderhaltung**
   - Bilder werden analysiert, aber nicht gespeichert
   - nur strukturierte Extrakte und Metadaten werden persistiert

7. **Personalisierung**
   - Profilwerte liegen in `settings.json`
   - alle sinnvollen Werte zur Zielableitung dürfen genutzt werden
   - abgeleitete Ziele bleiben manuell überschreibbar

8. **Health Boundary**
   - CLI = Rohdaten, Summen, Defizite, Zielvergleich
   - Skill = Coaching, Einordnung, Vorschläge

9. **Historie/Analytics**
   - Tagessicht ist primär
   - Wochenmittel gehören in den MVP

10. **Referenz auf Tracker-Standards**
   - Makro-/Kalorien-Tracking orientiert sich an gängigen Tracker-Apps
   - sichtbare Standardfelder aus dem bereitgestellten Screenshot: Kalorien, Gesamtfett, gesättigtes Fett, Transfett, mehrfach ungesättigtes Fett, einfach ungesättigtes Fett, Cholesterin, Natrium, Gesamtkohlenhydrate, Ballaststoffe, Gesamtzucker, Zuckerzusatz, Protein, Koffein, Alkohol, Vitamin D, Kalzium
   - für den MVP werden Kalorien, Protein, Fett, Kohlenhydrate und Ballaststoffe als Kern-Zielmetriken behandelt; zusätzliche Felder sollen schemafähig vorgesehen werden

---

## 16. Empfehlung für die nächste Iteration

Als nächstes sollten wir ein **konkretes Spec-Dokument** ableiten mit:
- finalem Datenmodell
- Eventformaten
- Zielschema
- Bewertungsheuristiken
- CLI-Kommandos und JSON-Ausgaben
- Hermes-/Skill-Flows
- MVP-Grenzen

Kurz: Erst Verhalten und Schnittstellen präzise machen, dann bauen.
