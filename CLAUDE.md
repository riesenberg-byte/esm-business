# esm.business – Hinweise für Claude

## Inhaltsläufe (App befüllen)

- **`ROUTINE.md` ist maßgeblich.** Bei jedem Inhaltslauf – ob per Routine oder von Hand angestoßen – zuerst `main` per `git pull` aktualisieren und `ROUTINE.md` in dieser Fassung vollständig lesen.
- Widerspricht ein Routine- oder Aufgaben-Prompt `ROUTINE.md` (etwa bei Kategorien, Aufrufen von `validate.py`, Commit-Format oder Suchregeln), gilt `ROUTINE.md`. Gespeicherte Prompts können veraltet sein; die Datei wird zwischen Läufen weiterentwickelt.
- Fehlt `ROUTINE.md` oder ist sie nicht lesbar: nichts veröffentlichen, nichts committen, Grund melden.

## Allgemein

- Es arbeiten oft mehrere Sessions parallel am Repo. Vor Änderungen `git pull`, vor dem Push erneut abgleichen; niemals force-pushen. Commits gehen direkt auf `main`.
- Vor jedem Push müssen grün sein: `python3 scripts/validate.py`, `python3 -m unittest discover -s tests`, `node tests/search.test.cjs`, `node tests/search-integration.test.cjs`, `node tests/archive-cache.test.cjs`.
- Kategorie-Schlüssel stehen an vier Stellen und müssen gemeinsam geändert werden: `CATS` in `index.html`, `validArchive` in `article-search.js`, `CATS`/`AI_LABELS` in `scripts/validate.py` und der Abschnitt „Kategorien" in `ROUTINE.md`. Bestehende Einträge in `data/items.json` und `data/archive.json` dann mit migrieren.
- Änderungen an Dateien der App-Hülle (`index.html`, `article-search.js`, `manifest.webmanifest`, Schrift, Icons) erfordern eine neue Cache-Version in `sw.js`, sonst liefert der Service Worker Besuchern die alte Fassung aus.
