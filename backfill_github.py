#!/usr/bin/env python3
"""从 4dresulthub 公开 JSON 补齐 4 家公司历史；只补缺失的 日期×公司。"""
import json, os, re
from urllib.request import urlopen, Request
from crawler_utils import save_json
from crawler_storage import update_dates_index, build_latest

BASE = 'https://raw.githubusercontent.com/Senekalata/4dresulthub/main/data/'
MAP = {'magnum': 'magnum', 'toto': 'toto',
       'damacai': 'damacai', 'singapore': 'singapore'}

def have_pairs(base='docs/data'):
    have = set(); adir = os.path.join(base, 'archive')
    for name in os.listdir(adir):
        if not re.fullmatch(r'\d{4}-\d{2}\.json', name): continue
        with open(os.path.join(adir, name), encoding='utf-8') as f:
            m = json.load(f)
        for ymd, cs in m.items():
            for c in cs: have.add((ymd, c))
    return have

def fetch(name):
    req = Request(BASE + name + '.json', headers={'User-Agent': '4d-crawler/2.0'})
    with urlopen(req, timeout=60) as r:
        return json.load(r)

def num(v):
    v = str(v or '').strip()
    return v if re.fullmatch(r'\d{4}', v) else None

def main():
    have = have_pairs(); added = 0
    for src, company in MAP.items():
        rows = fetch(src)
        n = 0
        for item in rows:
            ymd = (item.get('date') or '')[:10]
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', ymd) or (ymd, company) in have: continue
            one, two, three = (num(item.get(k)) for k in ('first', 'second', 'third'))
            if not (one and two and three): continue
            data = {'draw_date': ymd, 'draw_no': item.get('draw_number', ''),
                    '1st': one, '2nd': two, '3rd': three,
                    'special': [x for x in (item.get('special') or []) if num(x)],
                    'consolation': [x for x in (item.get('consolation') or []) if num(x)]}
            save_json(company, data); have.add((ymd, company)); added += 1; n += 1
        print(f'{src}: {len(rows)} 行，新增 {n}')
    update_dates_index()
    try: build_latest()
    except Exception as e: print(f'⚠️ build_latest: {e}')
    print(f'✅ 共新增 {added} 条')

if __name__ == '__main__': main()
