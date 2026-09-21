# Laufprotokoll

Spalten: Datum, neue Artikel, tatsächlich geprüfte (geöffnete) Kandidaten, Methode (`feeds`/`search`), Laufstatus (`ok`/`partial`/`blocked`), Events. Die monatliche Eventprüfung steht als `events_checked: JJJJ-MM` in der Event-Spalte, auch bei 0 neuen Events; `–` bedeutet, dass nicht geprüft wurde.

| Datum | Neu | Geprüft | Methode | Status | Events | Hinweise |
|---|---|---|---|---|---|---|
| 2026-09-20 | 0 | 0 | feeds | blocked | – | Alle 11 Feeds nicht erreichbar (403, Netzwerk-/Egress-Policy der Ausführungsumgebung), keine Kandidaten abrufbar |
| 2026-09-20 | 0 | 0 | feeds | blocked | – | Zweiter Lauf: gleiche Blockade weiterhin aktiv (403 auf allen 11 Feed-Hosts), Egress-Policy vermutlich dauerhaft, keine Kandidaten abrufbar |
| 2026-09-20 | 0 | 0 | search | partial | 2, events_checked: 2026-09 | Dritter Lauf: Ersatzweg genutzt (Feeds weiter 403), 5 Websuchen, Treffer der letzten 7 Tage geprüft – keiner erfüllte die Auswahlkriterien. Artikelabruf ebenfalls 403, daher keine Quelle geöffnet. 2 Events ergänzt (IT Summit München, Forum Digitale Souveränität Frankfurt) |
| 2026-09-21 | 7 | 2 | feeds | partial | – | 40 Kandidaten, 1 Feed fehlerhaft (Bing News: ServiceNow, ungültiges XML). 6 Artikel aus Anrisstext/Titel plus 2 Volltexte geprüft. Montags-Lückencheck: Kategorien eri/lshc/gps ohne Eintrag seit 30 Tagen – Websuche für gps (Agentic AI Hub Kommunen) ergänzt einen Eintrag, lshc ohne belastbare Quelle mit Zahl übersprungen |
