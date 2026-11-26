#!/usr/bin/env python3
"""补 2008-2022 Singapore 4D：4dlivetoday API -> archive。"""
import os, re, time
from datetime import datetime, timedelta
from crawler_utils import save_json
from crawler_http import SESSION

START, END, SLEEP = '2008-01-01', '2022-12-31', 1.0

def have(base='docs/data'):
    s = set(); adir = os.path.join(base, 'archive')
    for name in os.listdir(adir):
        if not re.fullmatch(r'\d{4}-\d{2}\.json', name): continue
        import json
        for ymd, cs in json.load(open(os.path.join(adir, name), encoding='utf-8')).items():
            if 'singapore' in cs: s.add(ymd)
    return s

def num(v):
    v = str(v or '').strip(); return v if re.fullmatch(r'\d{4}', v) else None

def main():
    done = have(); added = 0
    d, end = datetime.strptime(START, '%Y-%m-%d'), datetime.strptime(END, '%Y-%m-%d')
    while d <= end:
        ymd = d.strftime('%Y-%m-%d')
        if ymd not in done:
            try:
                r = SESSION.get('https://4dlivetoday.com/api/v1/results/' + ymd, timeout=25)
                r.raise_for_status()
                for item in r.json().get('data', {}).get('results', []):
                    if item.get('operator') != 'sg': continue
                    one, two, three = (num(item.get(k)) for k in ('first', 'second', 'third'))
                    if not (one and two and three): continue
                    save_json('singapore', {
                        'draw_date': ymd, 'draw_no': item.get('draw_no', ''),
                        '1st': one, '2nd': two, '3rd': three,
                        'special': [x for x in (item.get('special') or []) if num(x)],
                        'consolation': [x for x in (item.get('consolation') or []) if num(x)]})
                    done.add(ymd); added += 1; break
            except Exception as e:
                print(f'⚠️ {ymd}: {e}')
            time.sleep(SLEEP)
        d += timedelta(days=1)
    print(f'✅ Singapore 新增 {added} 天')

if __name__ == '__main__': main()
