"""RSS-2.0-Feeds (de/en) aus data/items.json; Links führen ins Lese-Blatt der App."""
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://' + (ROOT / 'CNAME').read_text(encoding='utf-8').strip() + '/'
MAX_ITEMS = 30
TEXT = {
    'de': {'desc': 'Relevante Meldungen zu Agentic AI, ESM rund um ServiceNow, digitaler Souveränität und Tech-Praxis.',
           'why': 'Warum relevant?', 'src': 'Quelle', 'tabs': {'ai': 'AI Adoption', 'esm': 'ESM & ServiceNow', 'sov': 'Souveränität', 'tech': 'Tech-Praxis'}},
    'en': {'desc': 'Relevant news on agentic AI, ESM around ServiceNow, digital sovereignty and tech in practice.',
           'why': 'Why it matters', 'src': 'Source', 'tabs': {'ai': 'AI adoption', 'esm': 'ESM & ServiceNow', 'sov': 'Sovereignty', 'tech': 'Tech in practice'}},
}


def _day(value):
    parts = [int(p) for p in value.split('-')] + [1, 1]
    return datetime(parts[0], parts[1], parts[2], tzinfo=timezone.utc)


def build_feed(items, lang):
    t = TEXT[lang]
    stamp = lambda i: i.get('added') or i['datum']
    latest = sorted(items, key=stamp, reverse=True)[:MAX_ITEMS]
    entries = []
    for i in latest:
        body = f"{i['kurz'][lang]}\n\n{t['why']} {i['rel'][lang]}\n\n{t['src']}: {i['qn']}"
        entries.append(
            '  <item>\n'
            f"   <title>{escape(i['titel'][lang])}</title>\n"
            f"   <link>{escape(SITE + '#' + i['id'])}</link>\n"
            f"   <guid isPermaLink=\"false\">esm-business-{escape(i['id'])}</guid>\n"
            f"   <category>{escape(t['tabs'][i['tab']])}</category>\n"
            f"   <pubDate>{format_datetime(_day(stamp(i)))}</pubDate>\n"
            f"   <description>{escape(body)}</description>\n"
            '  </item>\n')
    built = format_datetime(_day(stamp(latest[0]))) if latest else format_datetime(datetime(2026, 1, 1, tzinfo=timezone.utc))
    self_url = SITE + 'data/' + FEEDS[lang]
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n <channel>\n'
            '  <title>esm.business</title>\n'
            f'  <link>{SITE}</link>\n'
            f'  <atom:link href="{self_url}" rel="self" type="application/rss+xml"/>\n'
            f"  <description>{escape(t['desc'])}</description>\n"
            f'  <language>{lang}</language>\n'
            f'  <lastBuildDate>{built}</lastBuildDate>\n'
            + ''.join(entries) +
            ' </channel>\n</rss>\n')


FEEDS = {'de': 'feed.xml', 'en': 'feed-en.xml'}
