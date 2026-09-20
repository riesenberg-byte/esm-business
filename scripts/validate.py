#!/usr/bin/env python3
"""Prüft data/items.json und data/events.json, archiviert Altes, pflegt seen.json.
Aufruf: python3 scripts/validate.py [--seen candidates.json]   Exit 1 bei Fehlern."""
import json, re, sys
from datetime import date, timedelta, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent; DATA = ROOT / "data"
CATS = {"ai": {"consumer", "eri", "fs", "gps", "lshc", "tmt", "cross"},
        "esm": {"sn", "ma", "results", "industry", "market"},
        "sov": {"snsov", "cloud", "ai", "work"},
        "tech": {"mcp", "gov", "dev"}}
DATE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
KEEP_DAYS = 120

def load(p, d):
    try: return json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError: return d

def bi(o, name, maxlen, errs, iid):
    if not isinstance(o, dict) or not o.get("de") or not o.get("en"):
        errs.append(f"{iid}: '{name}' braucht de und en"); return
    for k in ("de", "en"):
        if len(o[k]) > maxlen: errs.append(f"{iid}: '{name}.{k}' zu lang ({len(o[k])}>{maxlen})")

def main():
    items = load(DATA / "items.json", []); events = load(DATA / "events.json", []); errs = []
    ids, urls = set(), set()
    for i in items:
        iid = i.get("id", "?")
        if iid in ids: errs.append(f"doppelte id {iid}")
        ids.add(iid)
        urls.add(i.get("quelle"))
        if i.get("tab") not in CATS: errs.append(f"{iid}: unbekannter tab"); continue
        if i.get("cat") not in CATS[i["tab"]]: errs.append(f"{iid}: cat passt nicht zu tab")
        if not DATE.match(str(i.get("datum", ""))): errs.append(f"{iid}: datum ungültig")
        if i.get("added") and not re.match(r"^\d{4}-\d{2}-\d{2}$", i["added"]): errs.append(f"{iid}: added ungültig")
        if i.get("rel_score") not in (1, 2, 3): errs.append(f"{iid}: rel_score 1–3")
        if not str(i.get("quelle", "")).startswith("https://"): errs.append(f"{iid}: quelle muss https sein")
        if not i.get("qn"): errs.append(f"{iid}: qn (Quellenname) fehlt")
        bi(i.get("titel"), "titel", 110, errs, iid); bi(i.get("kurz"), "kurz", 480, errs, iid); bi(i.get("rel"), "rel", 260, errs, iid)
        if i.get("metric"): bi(i["metric"], "metric", 14, errs, iid); bi(i.get("msub"), "msub", 50, errs, iid)
        if i.get("sub"): bi(i["sub"], "sub", 30, errs, iid)
    for e in events:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", e.get("datum", "")): errs.append(f"Event {e.get('titel')}: datum")
        if not str(e.get("url", "")).startswith("https://"): errs.append(f"Event {e.get('titel')}: url")
    if errs:
        print("FEHLER:\n- " + "\n- ".join(errs)); sys.exit(1)

    # Archivieren: Einträge, die älter als KEEP_DAYS hinzugefügt wurden
    limit = (date.today() - timedelta(days=KEEP_DAYS)).isoformat()
    old = [i for i in items if i.get("added") and i["added"] < limit]
    if old:
        arch = load(DATA / "archive.json", []); arch.extend(old)
        (DATA / "archive.json").write_text(json.dumps(arch, ensure_ascii=False, indent=1), encoding="utf-8")
        items = [i for i in items if i not in old]
    # Vergangene Events älter als 14 Tage entfernen
    ev_limit = (date.today() - timedelta(days=14)).isoformat()
    events = [e for e in events if (e.get("bis") or e["datum"]) >= ev_limit]
    (DATA / "items.json").write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    (DATA / "events.json").write_text(json.dumps(events, ensure_ascii=False, indent=1), encoding="utf-8")

    # Geprüfte Kandidaten merken, damit sie nicht erneut Tokens kosten
    if "--seen" in sys.argv:
        cand = load(ROOT / sys.argv[sys.argv.index("--seen") + 1], [])
        seen = load(DATA / "seen.json", [])
        known = {s["url"] for s in seen}
        today = date.today().isoformat()
        seen += [{"url": c["url"], "am": today} for c in cand if c["url"] not in known]
        cut = (date.today() - timedelta(days=45)).isoformat()
        seen = [s for s in seen if s["am"] >= cut]
        (DATA / "seen.json").write_text(json.dumps(seen, ensure_ascii=False, indent=0), encoding="utf-8")
    meta = {"aktualisiert": datetime.now(timezone.utc).isoformat(timespec="minutes"),
            "artikel": len(items),
            "letzter_artikel": max((i.get("added") or "" for i in items), default="")}
    (DATA / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK: {len(items)} Artikel, {len(events)} Events" + (f", {len(old)} archiviert" if old else ""))

if __name__ == "__main__":
    main()
