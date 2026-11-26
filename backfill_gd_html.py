#!/usr/bin/env python3
"""用 4dlivetoday HTML 结果页补 grand_dragon，并发版。"""
import os, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta

import requests
import check_local_gaps as cg
from crawler_utils import save_json

START, END = '2020-04-11', '2025-12-31'
WORKERS = int(os.getenv('GD_HTML_WORKERS', '3'))


def parse_gd(html):
    pos = html.find('<header class="pagehead"')
    chunks = html[pos:].split('<section class="board draw')[1:]
    c = next((x for x in chunks if '>Grand Dragon 4D</h2>' in x), None)
    if not c:
        return None
    first = ''.join(re.findall(r'seg7__d[^>]*>(\d)<', c))
    rest = re.findall(r'seg7--amber[^>]*>(\d{4})<', c)
    if len(first) != 4 or len(rest) < 2:
        return None
    return {
        'draw_no': (re.search(r'>(\d{3,6})\s*(?:<!-- -->)?\s*·', c) or [None, ''])[1],
        '1st': first, '2nd': rest[0], '3rd': rest[1],
        'special': re.findall(r'seg7--special[^>]*>(\d{4})<', c),
        'consolation': re.findall(r'seg7--muted[^>]*>(\d{4})<', c),
    }


def fetch(ymd):
    for attempt in range(4):
        try:
            r = requests.get('https://4dlivetoday.com/en/results/' + ymd,
                             timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
            if r.status_code == 404:
                return ymd, None
            if r.status_code == 200:
                return ymd, parse_gd(r.text)
            if r.status_code == 429:
                wait = 20 * (attempt + 1)
                print(f'  ⏳ 429 {ymd} 等 {wait}s', flush=True)
                time.sleep(wait)
                continue
            return ymd, None
        except Exception as e:
            if attempt == 3:
                print('  失败', ymd, str(e)[:60], flush=True)
            time.sleep(5 * (attempt + 1))
    return ymd, None


def main():
    have = cg.load()
    gd = set(have.get('grand_dragon', []))
    d, start = date.fromisoformat(END), date.fromisoformat(START)
    dates = []
    while d >= start:
        s = d.isoformat()
        if s not in gd:
            dates.append(s)
        d -= timedelta(days=1)
    print(f'待补 {len(dates)} 天，并发 {WORKERS}', flush=True)
    added = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(fetch, x) for x in dates]
        for i, fut in enumerate(as_completed(futs), 1):
            ymd, row = fut.result()
            if row:
                save_json('grand_dragon', {'draw_date': ymd, **row})
                gd.add(ymd)
                added += 1
            if i % 100 == 0 or i == len(dates):
                print(f'  进度 {i}/{len(dates)}，新增 {added}', flush=True)
    print(f'✅ 完成：新增 {added} 条', flush=True)


if __name__ == '__main__':
    main()
