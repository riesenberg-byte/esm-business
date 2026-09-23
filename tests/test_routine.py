import contextlib
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import fetch_candidates as feeds
import feed
import validate
import xml.etree.ElementTree as ET
from common import norm_url


class RoutineTests(unittest.TestCase):
    def setUp(self):
        self.items = json.loads((ROOT/'data/items.json').read_text())
        self.events = json.loads((ROOT/'data/events.json').read_text())
        self.legacy = json.loads((ROOT/'data/legacy.json').read_text())
        self.item = {'tab': 'sov', 'cat': 'cloud', 'id': 'atos-stackit', 'rel_score': 2, 'added': '2026-09-14', 'datum': '2026-09-03', 'region': 'EU', 'metric': None, 'titel': {'de': 'Atos vertreibt und integriert künftig STACKIT', 'en': 'Atos to resell and integrate STACKIT'}, 'kurz': {'de': 'Atos und Schwarz Digits haben in München eine Partnerschaft geschlossen: Atos verkauft die STACKIT-Plattform weiter und bindet sie in Kundenlandschaften ein.', 'en': 'Atos and Schwarz Digits signed a partnership in Munich: Atos will resell the STACKIT platform and integrate it into client landscapes.'}, 'rel': {'de': 'Souveräne Clouds kommen über große Integratoren in die Breite. Service-Management muss hybride Landschaften mit US- und EU-Plattformen abdecken.', 'en': 'Sovereign clouds are going mainstream through large integrators. Service management must cover hybrid landscapes with US and EU platforms.'}, 'quelle': 'https://www.drweb.de/atos-stackit-souveraene-cloud/', 'qn': 'Dr. Web Magazin'}

    def test_existing_data(self):
        errors, warnings = validate.validate(self.items,self.events,self.legacy)
        self.assertEqual(errors,[])

    def test_atom_summary_link_and_publication_date(self):
        raw=b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>ServiceNow</title><link rel="self" href="https://example.com/api"/><link rel="alternate" href="https://example.com/article"/><summary>Important summary</summary><updated>2026-09-20T00:00:00Z</updated><published>2026-09-19T00:00:00Z</published></entry></feed>'''
        entry=list(feeds.entries(raw))[0]
        self.assertEqual(entry[1:4],('https://example.com/article','Important summary','2026-09-19T00:00:00Z'))

    def test_invalid_values_rejected(self):
        for key,value in [('datum','2026-99-99'),('region','INVALID'),('titel',{'de':'x'*100,'en':'ok'}),('added',None),('quelle','https://'),('rel_score',True)]:
            with self.subTest(field=key):
                item=copy.deepcopy(self.item);item[key]=value
                self.assertTrue(validate.validate([item],[],{})[0])

    def test_feed_is_valid_rss_linking_into_app(self):
        item=copy.deepcopy(self.item);item.update(id='amp-test',added='2099-01-01',titel={'de':'A & B <C>','en':'A & B <C>'})
        root=ET.fromstring(feed.build_feed(self.items+[item],'de'))
        entries=root.findall('channel/item')
        self.assertLessEqual(len(entries),feed.MAX_ITEMS)
        self.assertEqual(entries[0].findtext('title'),'A & B <C>')
        self.assertEqual(entries[0].findtext('link'),feed.SITE+'#amp-test')
        self.assertTrue(all(e.findtext('link').startswith(feed.SITE+'#') for e in entries))

    def test_sub_is_optional_but_must_add_detail(self):
        item=copy.deepcopy(self.item);item.update(tab='ai',cat='gps')
        self.assertEqual(validate.validate([item],[],{})[0],[])
        item['sub']={'de':'Kommunalverwaltung','en':'Local government'}
        self.assertEqual(validate.validate([item],[],{})[0],[])
        item['sub']={'de':'Öffentlicher Sektor','en':'Public sector'}
        self.assertTrue(validate.validate([item],[],{})[0])

    def test_legacy_cannot_grant_new_article_exception(self):
        item=copy.deepcopy(self.item);item['id']='new-story';item.pop('added');item['datum']='2026-09'
        self.assertTrue(validate.validate([item],[],self.legacy)[0])

    def test_invalid_event_end(self):
        event={'datum': '2026-09-24', 'tag': {'de': 'ServiceNow', 'en': 'ServiceNow'}, 'titel': {'de': 'Brazil Early Availability', 'en': 'Brazil Early Availability'}, 'ort': {'de': 'Release-Meilenstein', 'en': 'Release milestone'}, 'note': {'de': 'Build Agent ohne Installation ausprobieren.', 'en': 'Try Build Agent with nothing to install.'}, 'url': 'https://www.servicenow.com/community/servicenow-otto-for-creator/what-s-new-in-servicenow-otto-for-creator-brazil-ea-release/ta-p/3596068'};event['bis']='2020-01-01'
        self.assertTrue(validate.validate([], [event], {})[0])

    def test_normalization_preserves_destination(self):
        self.assertEqual(norm_url('https://www.example.com/story/?utm_source=a&b=2'), 'https://www.example.com/story/?b=2')
        self.assertEqual(norm_url('https://www.bing.com/news/apiclick?url=https%3A%2F%2Fexample.com%2Fa'), 'https://example.com/a')

    def test_validation_is_read_only(self):
        before={p:p.read_bytes() for p in (ROOT/'data').glob('*.json')}
        subprocess.run([sys.executable,str(ROOT/'scripts/validate.py')],check=True,capture_output=True)
        self.assertEqual(before,{p:p.read_bytes() for p in before})

    def test_blocked_does_not_refresh_success_and_missing_input_does_not_write(self):
        with tempfile.TemporaryDirectory() as td:
            data=Path(td)
            for name,value in [('items',self.items),('events',self.events),('legacy',self.legacy),('seen',[]),('meta',{'letzte_recherche':'2026-09-19T10:00+00:00','aktualisiert':'2026-09-19T10:00+00:00'})]:
                (data/(name+'.json')).write_text(json.dumps(value))
            with patch.object(validate,'DATA',data),patch.object(sys,'argv',['validate','--apply','--status','blocked','--method','feeds']),contextlib.redirect_stdout(io.StringIO()):
                validate.main()
            meta=json.loads((data/'meta.json').read_text())
            self.assertEqual(meta['letzte_recherche'],'2026-09-19T10:00+00:00')
            self.assertEqual(meta['laufstatus'],'blocked')
            self.assertTrue(ET.fromstring((data/'feed.xml').read_bytes()).findall('channel/item'))
            before={p:p.read_bytes() for p in data.glob('*.json')}
            with patch.object(validate,'DATA',data),patch.object(sys,'argv',['validate','--apply','--status','ok','--method','search','--seen',str(data/'missing.json')]),contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(FileNotFoundError):validate.main()
            self.assertEqual(before,{p:p.read_bytes() for p in before})

if __name__=='__main__': unittest.main()
