"""Shared URL and atomic JSON helpers (standard library only)."""
import html
import json
import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse, parse_qsl, parse_qs, urlencode, urlunparse


def norm_url(value):
    q = urlparse(html.unescape(value.strip()))
    if (q.hostname or '').lower() in {'bing.com', 'www.bing.com'} and 'apiclick' in q.path:
        real = parse_qs(q.query).get('url', [''])[0]
        if real:
            q = urlparse(real)
    params = sorted((k, v) for k, v in parse_qsl(q.query, keep_blank_values=True)
                    if not k.lower().startswith(('utm_', 'wt_', 'cmp', 'ocid')))
    return urlunparse((q.scheme.lower(), q.netloc.lower(), q.path, '', urlencode(params), ''))


def write_text(path, text):
    path = Path(path)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(text)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def write_json(path, value):
    write_text(path, json.dumps(value, ensure_ascii=False, indent=1) + '\n')
