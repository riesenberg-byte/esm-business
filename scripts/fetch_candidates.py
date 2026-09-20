#!/usr/bin/env python3
"""Vorfilter ohne KI: holt RSS/Atom-Feeds, filtert per Stichwort, entfernt Bekanntes.
Ergebnis: candidates.json (nicht committen). Nur Standardbibliothek."""
import json, re, sys, html, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
UA = "Mozilla/5.0 (esm.business feed reader)"

def load(p, default):
    try: return json.loads(p.read_text(encoding="utf-8"))
    except Exception: return default

def norm_url(u):
    u = html.unescape(u.strip())
    q = urllib.parse.urlparse(u)
    if "bing.com" in q.netloc and "apiclick" in q.path:          # Bing-Weiterleitung auflösen
        real = urllib.parse.parse_qs(q.query).get("url", [""])[0]
        if real: u = real; q = urllib.parse.urlparse(u)
    params = [(k, v) for k, v in urllib.parse.parse_qsl(q.query) if not k.lower().startswith(("utm_", "wt_", "cmp", "ocid"))]
    return urllib.parse.urlunparse((q.scheme, q.netloc.lower().removeprefix("www."), q.path.rstrip("/"), "", urllib.parse.urlencode(params), ""))

def text(el):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape("".join(el.itertext()) if el is not None else ""))).strip()

def parse_date(s):
    if not s: return None
    try: return parsedate_to_datetime(s)
    except Exception: pass
    try: return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception: return None

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()

def entries(raw):
    root = ET.fromstring(raw)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for it in root.iter("item"):
        yield text(it.find("title")), (it.findtext("link") or "").strip(), text(it.find("description")), it.findtext("pubDate")
    for it in root.iter("{http://www.w3.org/2005/Atom}entry"):
        link = it.find("a:link[@rel='alternate']", ns) or it.find("a:link", ns)
        yield (text(it.find("a:title", ns)), link.get("href") if link is not None else "",
               text(it.find("a:summary", ns) or it.find("a:content", ns)),
               it.findtext("a:updated", namespaces=ns) or it.findtext("a:published", namespaces=ns))

def score(s, kw):
    s = s.casefold(); total = 0; hits = []
    for weight, words in kw.items():
        for w in words:
            stem = w.endswith("*"); w0 = w.rstrip("*").casefold()
            if re.search(r"(?<![\w-])" + re.escape(w0) + ("" if stem else r"(?![\w-])"), s):
                total += int(weight); hits.append(w)
    return total, hits

def main():
    cfg = load(DATA / "sources.json", {})
    items = load(DATA / "items.json", [])
    seen = load(DATA / "seen.json", [])
    known = {norm_url(i["quelle"]) for i in items} | {s["url"] for s in seen}
    cutoff = datetime.now(timezone.utc) - timedelta(days=cfg.get("max_age_days", 6))
    excl = [e.casefold() for e in cfg.get("exclude", [])]
    out, status, titles = [], {}, set()
    for f in cfg.get("feeds", []):
        try:
            raw = fetch(f["url"]); n = 0
            for title, link, desc, date in entries(raw):
                if not title or not link: continue
                u = norm_url(link)
                if u in known: continue
                d = parse_date(date)
                if d and d.tzinfo is None: d = d.replace(tzinfo=timezone.utc)
                if d and d < cutoff: continue
                blob = f"{title} {desc}"
                if any(e in blob.casefold() for e in excl): continue
                sc, hits = score(blob, cfg.get("keywords", {}))
                if sc < 3: continue
                key = re.sub(r"\W+", "", title.casefold())[:60]
                if key in titles: continue
                titles.add(key); n += 1
                out.append({"url": u, "titel": title[:200], "teaser": desc[:280], "datum": d.date().isoformat() if d else None,
                            "feed": f["name"], "score": sc, "treffer": hits[:6]})
            status[f["name"]] = {"ok": True, "neu": n}
        except Exception as e:
            status[f["name"]] = {"ok": False, "fehler": str(e)[:160]}
    out.sort(key=lambda c: c["datum"] or "", reverse=True)
    out.sort(key=lambda c: c["score"], reverse=True)
    out = out[: cfg.get("max_candidates", 40)]
    (ROOT / "candidates.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (DATA / "feed_status.json").write_text(json.dumps({"stand": datetime.now(timezone.utc).isoformat(timespec="minutes"), "feeds": status}, ensure_ascii=False, indent=1), encoding="utf-8")
    bad = [k for k, v in status.items() if not v["ok"]]
    print(f"{len(out)} Kandidaten aus {len(status)-len(bad)}/{len(status)} Feeds." + (f" Fehler: {', '.join(bad)}" if bad else ""))

if __name__ == "__main__":
    main()
