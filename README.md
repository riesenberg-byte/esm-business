# esm.business

Agentic AI Adoption und ESM-Transformation – eine schlanke PWA mit Meldungen zu AI Adoption, ESM & ServiceNow, digitaler Souveränität und Tech-Praxis. Statische Seite, Inhalte in `data/*.json`, befüllt von einer Claude-Routine.

## Aufbau

| Pfad | Inhalt |
|---|---|
| `index.html` | App (lädt `data/items.json` und `data/events.json`) |
| `sw.js`, `manifest.webmanifest`, `icons/` | PWA: Offline-Hülle, Installierbarkeit, Icons |
| `fonts/` | Schibsted Grotesk, lokal ausgeliefert (SIL Open Font License) |
| `data/items.json` | Artikel |
| `data/events.json` | Events |
| `data/sources.json` | Feeds, Stichworte, Ausschlüsse für den Vorfilter |
| `data/seen.json` | bereits geprüfte Links (spart Tokens), wird automatisch gepflegt |
| `data/feed_status.json` | Status der Feeds nach jedem Lauf |
| `data/meta.json` | Zeitpunkt der letzten Aktualisierung (in der App angezeigt) |
| `scripts/fetch_candidates.py` | Vorfilter ohne KI |
| `scripts/validate.py` | Prüfung, Archivierung, Pflege von `seen.json` |
| `ROUTINE.md` | Arbeitsanweisung für die Claude-Routine |
| `RUNLOG.md` | eine Zeile pro Lauf |

## Lokal ansehen

```bash
python3 -m http.server 8080
# dann http://localhost:8080 öffnen
```

## Veröffentlichung über GitHub Pages

1. Repo `esm-business` auf GitHub anlegen und diesen Ordner pushen (siehe unten).
2. *Settings → Pages*: Source „Deploy from a branch", Branch `main`, Ordner `/ (root)`.
3. *Custom domain*: `esm.business` (die Datei `CNAME` ist schon da). Beim Domain-Anbieter:
   - `A`-Records für `esm.business` auf `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - `CNAME` für `www` auf `<github-benutzer>.github.io`
4. Wenn das Zertifikat ausgestellt ist: „Enforce HTTPS" aktivieren.
5. Empfohlen: Domain unter *Settings → Pages → Verified domains* im GitHub-Profil verifizieren.

Vor dem Livegang `impressum.html` und `datenschutz.html` ausfüllen bzw. prüfen.

## Routine einrichten

In Claude Code (Web) eine Routine anlegen:
- **Repository:** dieses Repo, mit Schreibrecht auf `main`
- **Zeitplan:** Mo, Mi, Fr um 06:30 (Europe/Berlin)
- **Netzwerk:** Zugriff auf die Feed-Domains aus `data/sources.json` und auf Artikelseiten erlauben
- **Prompt:**
  > Lies ROUTINE.md im Repository und führe den Lauf für heute genau danach aus. Halte dich strikt an die Grenzen für Anzahl, Abrufe und Länge.

Erster Test: Routine einmal manuell starten, danach `RUNLOG.md` und `data/feed_status.json` prüfen. Nicht erreichbare Feeds in `data/sources.json` korrigieren oder entfernen.

## Qualität und Laufstatus

`python3 scripts/validate.py` prüft nur und verändert keine Dateien.
`python3 -m unittest discover -s tests` prüft Parser, Datenregeln und Schreibverhalten.
Die vollständigen Schreibbefehle und Statusregeln stehen in ROUTINE.md.

`data/legacy.json` hält die unveränderten Datums-Ausnahmen des übernommenen Bestands fest; neue Artikel müssen vollständige Datumsangaben haben. Gemeinsame Quellen erzeugen Warnungen zur redaktionellen Prüfung.

Bei `Tunnel connection failed: 403 Forbidden` zunächst die erlaubten Netzwerkziele der Routine-Umgebung prüfen. Danach dort einen manuellen Feed-Abruf testen. Änderungen im Repository können diese Umgebungseinstellungen nicht freischalten. Der Websuche-Ersatzweg funktioniert nur, wenn entsprechende Werkzeuge verfügbar sind.

Metadaten unterscheiden letzten Versuch, letzte erfolgreiche (ggf. eingeschränkte) Recherche und Laufstatus. Ein technischer Ausfall aktualisiert den Recherchezeitpunkt nicht. `letzter_artikel` zeigt das letzte bekannte Aufnahmedatum; Eventänderungen stehen zusätzlich im Laufprotokoll.

## Suche und Archiv

Das Suchfeld durchsucht Titel, Kurztext, Einordnung, Teilsektor und Quellenname in beiden Sprachen über alle Artikelthemen. Mehrere Suchwörter müssen alle vorkommen; Groß-/Kleinschreibung und Akzente werden ignoriert. Thema und Kategorie begrenzen die Treffer. Suchbegriffe werden weder gespeichert noch übertragen.

„Archiv einbeziehen“ lädt `data/archive.json` bei Bedarf und erweitert Suche und Themenansichten. Die Merkliste lädt das Archiv unabhängig vom Schalter, wenn gespeicherte IDs nicht mehr in den aktuellen Artikeln stehen. Fehler werden mit Wiederholungsmöglichkeit angezeigt; gespeicherte IDs bleiben erhalten. Bereits geladene Archivdaten stehen über den Service Worker auch offline zur Verfügung. Die bestehende 120-Tage-Archivierung bleibt unverändert.

Prüfen: `node tests/search.test.cjs`, `node tests/search-integration.test.cjs` und `node tests/archive-cache.test.cjs`. Die Integrationstests führen den Anwendungscode mit einer simulierten DOM- und Netzwerkumgebung aus; sie ersetzen keine visuelle Browserprüfung.
