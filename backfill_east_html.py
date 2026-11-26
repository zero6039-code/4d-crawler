#!/usr/bin/env python3
"""用 HTML 页补 sabah/sarawak_cashsweep/sandakan；无板块或 404=没开奖。"""
import json, os, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import check_local_gaps as cg
from crawler_utils import save_json

TARGET = ['sabah', 'sarawak_cashsweep', 'sandakan']
HEAD = {
    'sabah': 'Sabah 88 4D',
    'sarawak_cashsweep': 'Sarawak Cash Sweep',
    'sandakan': 'Sandakan STC 4D',
}
WORKERS = int(os.getenv('EAST_HTML_WORKERS', '3'))


def parse_blocks(html):
    pos = html.find('<header class="pagehead"')
    chunks = html[pos:].split('<section class="board draw')[1:]
    out = {}
    for c in chunks:
        for comp, name in HEAD.items():
            if '>' + name + '</h2>' not in c:
                continue
            first = ''.join(re.findall(r'seg7__d[^>]*>(\d)<', c))
            grab = lambda cls: re.findall(cls + r'[^>]*>(\d{4})<', c)
            rest = grab(r'seg7--amber')
            if len(first) != 4 or len(rest) < 2:
                continue
            out[comp] = {
                'draw_no': (re.search(r'>(\d{3,6})\s*(?:<!-- -->)?\s*·', c) or [None, ''])[1],
                '1st': first, '2nd': rest[0], '3rd': rest[1],
                'special': grab(r'seg7--special'),
                'consolation': grab(r'seg7--muted'),
            }
    return out


def fetch(ymd):
    for attempt in range(4):
        try:
            r = requests.get('https://4dlivetoday.com/en/results/' + ymd,
                             timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
            if r.status_code == 404:
                return ymd, {}
            if r.status_code == 200:
                return ymd, parse_blocks(r.text)
            if r.status_code == 429:
                wait = 20 * (attempt + 1)
                print(f'  ⏳ 429 {ymd} 等 {wait}s', flush=True)
                time.sleep(wait)
                continue
            return ymd, {}
        except Exception as e:
            if attempt == 3:
                print('  失败', ymd, str(e)[:60], flush=True)
            time.sleep(5 * (attempt + 1))
    return ymd, {}


def main():
    have = cg.load()
    with open('gaps_east.json', encoding='utf-8') as f:
        gaps = json.load(f)
    tasks = {}
    for c in TARGET:
        pool = set(gaps[c]['missing']) | set(gaps[c]['special_candidates'])
        for d in pool:
            if d not in have[c]:
                tasks.setdefault(d, set()).add(c)
    dates = sorted(tasks, reverse=True)
    print(f'待查 {len(dates)} 天（近→远），并发 {WORKERS}', flush=True)
    added = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(fetch, d) for d in dates]
        for i, fut in enumerate(as_completed(futs), 1):
            ymd, rows = fut.result()
            for comp, row in rows.items():
                if comp not in tasks[ymd] or ymd in have[comp]:
                    continue
                save_json(comp, {'draw_date': ymd, **row})
                have[comp].add(ymd)
                added += 1
            if i % 50 == 0 or i == len(dates):
                print(f'  进度 {i}/{len(dates)}，新增 {added}', flush=True)
    print(f'✅ 完成：新增 {added} 条', flush=True)
    for c in TARGET:
        print(f'{c:20s} 本地现有 {len(have[c])} 条', flush=True)


if __name__ == '__main__':
    main()
