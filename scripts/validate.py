#!/usr/bin/env python3
"""Read-only validation by default; --apply performs maintenance after validation."""
import argparse
import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse
from common import norm_url, write_json

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
AI_LABELS = {'ind': 'Industrie & Handel', 'fs': 'Banken & Versicherungen', 'gps': 'Öffentlicher Sektor',
             'lshc': 'Gesundheit', 'tmt': 'Telko & IT', 'cross': 'Studien'}
CATS = {'ai': set(AI_LABELS), 'esm': {'sn','results','market'},
        'sov': {'snsov','cloud','ai'}, 'tech': {'mcp','gov','dev'}}
REGIONS = {'DE','DACH','EU','US','Global','CH','AT'}


def load(path, default=None):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        if default is not None:
            return default
        raise


def valid_date(value):
    try:
        return isinstance(value, str) and bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}', value)) and date.fromisoformat(value) is not None
    except ValueError:
        return False


def valid_url(value):
    try:
        u = urlparse(value)
        return isinstance(value, str) and u.scheme == 'https' and bool(u.hostname) and not u.username and not any(c.isspace() or c in '\"<>' for c in value)
    except (ValueError, TypeError):
        return False


def validate(items, events, legacy):
    errors, warnings, ids, urls = [], [], set(), {}
    def bi(obj, field, limit, label):
        if not isinstance(obj, dict) or any(not isinstance(obj.get(k), str) or not obj[k].strip() or len(obj[k]) > limit for k in ('de','en')):
            errors.append(f'{label}: {field} benötigt de/en, 1–{limit} Zeichen')
    if not isinstance(items, list) or not isinstance(events, list):
        return ['items/events müssen Listen sein'], []
    for item in items:
        if not isinstance(item, dict):
            errors.append('Artikel muss Objekt sein'); continue
        iid = item.get('id'); label = str(iid)
        if not isinstance(iid, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', iid):
            errors.append(f'{label}: ungültige ID'); continue
        if iid in ids: errors.append(f'{iid}: doppelte ID')
        ids.add(iid)
        old = legacy.get('items', {}).get(iid, {})
        if item.get('tab') not in CATS or item.get('cat') not in CATS.get(item.get('tab'), set()): errors.append(f'{iid}: tab/cat ungültig')
        if not valid_date(item.get('datum')) and not (old.get('datum') and item.get('datum') == old['datum']): errors.append(f'{iid}: datum muss gültiges YYYY-MM-DD sein')
        if not valid_date(item.get('added')) and not (old.get('missing_added') and 'added' not in item): errors.append(f'{iid}: added fehlt/ungültig')
        if valid_date(item.get('added')) and item['added'] > date.today().isoformat(): errors.append(f'{iid}: added liegt in der Zukunft')
        if item.get('region') not in REGIONS: errors.append(f'{iid}: region ungültig')
        if type(item.get('rel_score')) is not int or item['rel_score'] not in (1,2,3): errors.append(f'{iid}: rel_score ungültig')
        if not valid_url(item.get('quelle')): errors.append(f'{iid}: quelle ungültig')
        else: urls.setdefault(norm_url(item['quelle']), []).append(iid)
        if not isinstance(item.get('qn'), str) or not item['qn'].strip(): errors.append(f'{iid}: qn fehlt')
        for field, limit in [('titel',90),('kurz',400),('rel',220)]: bi(item.get(field),field,limit,iid)
        if item.get('sub') is not None:
            if item.get('tab') != 'ai': errors.append(f'{iid}: sub nur bei ai')
            else:
                bi(item['sub'],'sub',30,iid)
                if isinstance(item['sub'], dict) and str(item['sub'].get('de','')).strip().casefold() == AI_LABELS.get(item.get('cat'),'').casefold():
                    errors.append(f'{iid}: sub wiederholt nur die Kategorie')
        if (item.get('metric') is None) != (item.get('msub') is None): errors.append(f'{iid}: metric/msub nur gemeinsam')
        if item.get('metric') is not None:
            bi(item['metric'],'metric',14,iid); bi(item.get('msub'),'msub',50,iid)
    for url, group in urls.items():
        if len(group)>1: warnings.append('Gemeinsame Quelle redaktionell prüfen: ' + ', '.join(group))
    event_keys = set()
    for event in events:
        if not isinstance(event, dict): errors.append('Event muss Objekt sein'); continue
        label = str(event.get('titel'))
        for field, limit in [('titel',150),('tag',100),('ort',150),('note',400)]: bi(event.get(field),field,limit,label)
        if not valid_date(event.get('datum')): errors.append(f'{label}: datum ungültig')
        if event.get('bis') is not None and (not valid_date(event['bis']) or str(event['bis']) < str(event.get('datum'))): errors.append(f'{label}: bis ungültig')
        if not valid_url(event.get('url')): errors.append(f'{label}: URL ungültig')
        else:
            key = (norm_url(event['url']), str(event.get('datum')))
            if key in event_keys: errors.append(f'{label}: doppeltes Event')
            event_keys.add(key)
    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--seen', type=Path, help='Nur tatsächlich geprüfte Kandidaten')
    parser.add_argument('--status', choices=['ok','partial','blocked'])
    parser.add_argument('--method', choices=['feeds','search'])
    args = parser.parse_args()
    if args.apply and (not args.status or not args.method): parser.error('--apply benötigt --status und --method')
    if not args.apply and (args.seen or args.status or args.method): parser.error('Schreiboptionen benötigen --apply')
    items, events = load(DATA/'items.json'), load(DATA/'events.json')
    legacy = load(DATA/'legacy.json', {})
    errors, warnings = validate(items, events, legacy)
    for warning in warnings: print('WARNUNG:', warning)
    if errors: raise SystemExit('FEHLER:\n- ' + '\n- '.join(errors))
    if args.apply:
        # Read and check every input before writing any file.
        seen = load(DATA/'seen.json', [])
        reviewed = load(args.seen) if args.seen else []
        for entry in seen:
            if not valid_url(entry.get('url')) or not valid_date(entry.get('am')): raise SystemExit('seen.json ungültig')
        for entry in reviewed:
            if not valid_url(entry.get('url')): raise SystemExit('Geprüfter Kandidat: URL ungültig')
        now = datetime.now(timezone.utc).isoformat(timespec='minutes')
        today = date.today().isoformat()
        merged = {norm_url(s['url']): s['am'] for s in seen}
        for entry in reviewed: merged[norm_url(entry['url'])] = today
        seen = [{'url':u,'am':d} for u,d in sorted(merged.items()) if d >= (date.today()-timedelta(days=45)).isoformat()]
        cutoff = (date.today()-timedelta(days=120)).isoformat()
        old = [i for i in items if (i.get('added') or legacy.get('retention_start', today)) < cutoff]
        archive = load(DATA/'archive.json', [])
        archived_ids = {i['id'] for i in archive}
        archive += [i for i in old if i['id'] not in archived_ids]
        items = [i for i in items if i not in old]
        events = [e for e in events if (e.get('bis') or e['datum']) >= (date.today()-timedelta(days=14)).isoformat()]
        meta = load(DATA/'meta.json', {})
        meta.update(letzter_versuch=now, laufstatus=args.status, methode=args.method, artikel=len(items), letzter_artikel=max((i.get('added','') for i in items),default=''))
        if args.status in ('ok','partial'):
            meta['letzte_recherche'] = now
            meta['aktualisiert'] = now
        write_json(DATA/'items.json', items); write_json(DATA/'events.json', events)
        if old: write_json(DATA/'archive.json', archive)
        write_json(DATA/'seen.json', seen); write_json(DATA/'meta.json', meta)
    print(f'OK: {len(items)} Artikel, {len(events)} Events' + ('; gespeichert' if args.apply else '; nur geprüft'))

if __name__ == '__main__':
    main()
