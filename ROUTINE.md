# Routine: esm.business befüllen

Du pflegst die News-App esm.business. Sie zeigt wenige, relevante Meldungen zu **Agentic AI Adoption**, **ESM-Transformation rund um ServiceNow**, **digitaler Souveränität** und **Tech-Praxis** – neutral, für Kunden wie Berater. Relevanz schlägt Menge. Arbeite sparsam: keine unnötigen Tool-Aufrufe, keine langen Überlegungen im Text.

## Ablauf

1. `python3 scripts/fetch_candidates.py` ausführen. Es entsteht `candidates.json` (max. 40 Schlagzeilen mit Anrisstext, Bekanntes ist schon aussortiert).
2. `candidates.json` lesen. **Sind es 0 Kandidaten und zeigt `data/feed_status.json` bei allen Feeds Fehler** (z. B. 403 durch die Netzwerkrichtlinie), dann nutze den Ersatzweg weiter unten. Bei einzelnen fehlerhaften Feeds normal weiterarbeiten und den Ausfall in Schritt 6 vermerken.
   Sonst: `candidates.json` auswerten. **Höchstens 6** Kandidaten auswählen, die die Kriterien unten erfüllen. Gibt es weniger als 2 gute: keine Artikel schreiben, aber Schritt 5 bis 7 trotzdem ausführen.
3. Für **höchstens 3** der Auswahl den Artikel mit web_fetch öffnen, wenn Anrisstext und Titel für Zahlen oder Einordnung nicht reichen. Sonst aus dem Anrisstext arbeiten. Keine freie Websuche – Ausnahme siehe „Montag".
4. Neue Einträge **am Anfang** von `data/items.json` einfügen (Schema unten). Bestehende Einträge nicht verändern.
5. `python3 scripts/validate.py --seen candidates.json` ausführen. Bei Fehlern korrigieren und erneut prüfen. Das Skript schreibt auch `data/meta.json` mit dem Aktualisierungszeitpunkt – immer mitcommitten, auch wenn es keine neuen Artikel gab.
6. Eine Zeile an `RUNLOG.md` anhängen: `| JJJJ-MM-TT | Anzahl neu | Anzahl Kandidaten | Auffälligkeiten, z. B. fehlerhafte Feeds aus data/feed_status.json |`
7. Commit **direkt auf `main`** (kein Arbeitsbranch, kein Pull Request) mit Nachricht `Inhalte JJJJ-MM-TT: N neu` und pushen. `candidates.json` nicht committen.

## Ersatzweg, wenn die Feeds blockiert sind

Die Werkzeuge `web_search` und `web_fetch` laufen nicht über die Sandbox und funktionieren auch dann, wenn `bash` keine Verbindung bekommt. In diesem Fall:

- Höchstens **5 Websuchen**, je eine pro Thema, mit dem aktuellen Monat in der Anfrage: ServiceNow, Agentic AI im deutschen Markt, ESM- und ITSM-Markt, souveräne Cloud, AI-Governance und Agenten-Steuerung.
- Nur Treffer der letzten 7 Tage berücksichtigen.
- Jeden Kandidaten gegen `data/items.json` (Feld `quelle`) und `data/seen.json` prüfen und Bekanntes verwerfen.
- Es gelten dieselben Grenzen wie sonst: höchstens 6 neue Artikel, höchstens 3 Artikel mit `web_fetch` öffnen, gleiche Auswahlkriterien, gleiche Schreibregeln.
- Die geprüften Links selbst in `data/seen.json` ergänzen (Format `{"url": "…", "am": "JJJJ-MM-TT"}`), da `--seen` hier keine Kandidatendatei hat.
- In `RUNLOG.md` vermerken, dass der Ersatzweg genutzt wurde.

**Montag zusätzlich:** Prüfe, welche Kategorie in `ai` in den letzten 30 Tagen keinen Eintrag bekam. Für bis zu 2 solche Lücken je **eine** Websuche (deutscher Markt bevorzugt) und ggf. je einen Eintrag.
**Erster Lauf im Monat zusätzlich:** Bis zu 3 neue öffentliche Events (Konferenzen, Messen, ServiceNow-Termine im DACH-Raum oder großen EU-Städten) per Websuche prüfen und in `data/events.json` eintragen. Nur mit bestätigtem Datum und offizieller URL.

## Auswahlkriterien

Aufnehmen, wenn mindestens zwei zutreffen:
- konkrete Wirkung oder Zahl (Einsparung, Zeit, Quote, Nutzerzahl, Umsatz)
- Bezug zum deutschen bzw. DACH-Markt
- Relevanz für ESM, ServiceNow, AI-Governance, Agenten-Steuerung oder Souveränität
- Produktivbetrieb statt Ankündigung oder Pilot ohne Ergebnis

Nicht aufnehmen: Börsenkurse und Kursziele, reine Marketingmeldungen ohne Substanz, Meinungsstücke ohne neue Fakten, Duplikate derselben Nachricht, Paywall-Artikel, deren Inhalt du nicht prüfen kannst.

`rel_score`: **3** = würde man Kollegen aktiv weiterleiten (klare Zahl plus hohe Relevanz oder wichtige Marktbewegung), **2** = solide und relevant, **1** = Randnotiz. Einträge mit 1 nur, wenn es in diesem Lauf sonst nichts gibt.

## Schema eines Eintrags

```json
{
 "tab": "ai | esm | sov | tech",
 "cat": "siehe Kategorien",
 "sub": {"de": "Teilsektor", "en": "Subsector"},
 "id": "kurzer-eindeutiger-slug",
 "datum": "Erscheinungsdatum des Artikels, JJJJ-MM-TT",
 "added": "heutiges Datum, JJJJ-MM-TT",
 "region": "DE | DACH | EU | US | Global | CH | AT",
 "rel_score": 2,
 "metric": {"de": "75 %", "en": "75%"},
 "msub": {"de": "kurze Erklärung der Zahl", "en": "…"},
 "titel": {"de": "…", "en": "…"},
 "kurz": {"de": "2–3 Sätze", "en": "…"},
 "rel": {"de": "1–2 Sätze: Warum relevant?", "en": "Why it matters"},
 "quelle": "https://…",
 "qn": "Name des Mediums"
}
```
`sub` nur bei `tab: ai`. `metric`/`msub` weglassen (auf `null` setzen), wenn die Quelle keine belastbare Zahl nennt – nie schätzen.

**Kategorien**
- `ai` (nach Branchen): `consumer` (Automotive, Handel, Konsumgüter, Transport), `eri` (Energie, Ressourcen, Industrie), `fs` (Banken, Versicherungen, Zahlungsverkehr), `gps` (öffentlicher Sektor), `lshc` (Gesundheit, Pharma), `tmt` (Technologie, Medien, Telko), `cross` (Studien, branchenübergreifend)
- `esm`: `sn` (ServiceNow-Plattform), `ma` (Acquisitions, z. B. Moveworks, Armis, Veza), `results` (belegte Projektergebnisse), `industry` (Branchenlösungen), `market` (Wettbewerber, andere AI Control Towers)
- `sov`: `snsov` (ServiceNow souverän betrieben), `cloud` (souveräne Cloud & Plattformen), `ai` (souveräne KI-Modelle), `work` (Arbeitsplatz & Verwaltung)
- `tech`: `mcp` (MCP & Integration), `gov` (Governance, Sicherheit, Architekturmuster), `dev` (Entwicklung, Releases)

## Schreibregeln

- Beide Sprachen in einem Durchgang, inhaltlich gleich, jeweils idiomatisch.
- **Eigene Worte.** Keine Sätze aus der Quelle übernehmen, keine Zitate, keine Satzstruktur nachbauen.
- `titel`: sachlich, max. 90 Zeichen, keine Clickbait-Formulierung.
- `kurz`: 2–3 Sätze, max. 400 Zeichen – was ist passiert, mit welcher Zahl.
- `rel` („Warum relevant?"): 1–2 Sätze, max. 220 Zeichen, neutral, für jede Leserin nützlich – keine Verkaufsansprache, kein „wir", keine Empfehlung für einen bestimmten Anbieter.
- Herstellerangaben als solche kennzeichnen („laut ServiceNow").
- Deutsche Zahlenformate im DE-Text (75 %, 2,5 Mio.), englische im EN-Text (75%, 2.5m).
- Keine Personen außer öffentlichen Rollenträgern in offizieller Funktion.
