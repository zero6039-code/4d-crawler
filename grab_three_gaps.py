#!/usr/bin/env python3
"""从 gaps_three.json 读取缺失+特别日候选，并发抓取，只补缺失的 日期×公司。"""
import json, os, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import check_local_gaps as cg
from crawler_utils import save_json

TARGET = ['magnum', 'toto', 'damacai']
OP = {'magnum': 'magnum', 'toto': 'toto', 'damacai': 'damacai'}
WORKERS = int(os.getenv('GAP_WORKERS', '2'))
KEEP_STOP = os.getenv('KEEP_STOP', '') == '1'
SKIP = [('2020-03-18', '2020-06-14'), ('2021-06-02', '2021-09-12')]


def num(v):
    v = str(v or '').strip()
    return v if re.fullmatch(r'\d{4}', v) else None


def in_skip(s):
    return not KEEP_STOP and any(a <= s <= b for a, b in SKIP)


def fetch(ymd):
    for attempt in range(4):
        try:
            r = requests.get('https://4dlivetoday.com/api/v1/results/' + ymd,
                             timeout=15, headers={'User-Agent': '4d-crawler/2.0'})
            r.raise_for_status()
            return ymd, r.json().get('data', {}).get('results', [])
        except Exception as e:
            if '429' in str(e):
                print(f'  ⏳ 429 {ymd}', flush=True)
                if attempt < 3:
                    time.sleep(8 * (attempt + 1))
                    continue
            return ymd, []
    return ymd, []


def main():
    have = cg.load()
    with open('gaps_three.json', encoding='utf-8') as f:
        gaps = json.load(f)
    tasks = {}
    for c in TARGET:
        for d in gaps[c]['missing'] + gaps[c]['special_candidates']:
            if in_skip(d) or d in have[c]:
                continue
            tasks.setdefault(d, set()).add(c)
    dates = sorted(tasks, reverse=True)
    print(f'待抓 {len(dates)} 天（已排除停开段；KEEP_STOP=1 可保留），并发 {WORKERS}')
    added = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(fetch, d) for d in dates]
        for i, fut in enumerate(as_completed(futs), 1):
            ymd, results = fut.result()
            for item in results:
                c = OP.get(item.get('operator'))
                if c not in tasks[ymd]:
                    continue
                one, two, three = (num(item.get(k)) for k in ('first', 'second', 'third'))
                if not (one and two and three):
                    continue
                save_json(c, {
                    'draw_date': ymd, 'draw_no': item.get('draw_no', ''),
                    '1st': one, '2nd': two, '3rd': three,
                    'special': [x for x in (item.get('special') or []) if num(x)],
                    'consolation': [x for x in (item.get('consolation') or []) if num(x)],
                })
                have[c].add(ymd)
                added += 1
            if i % 50 == 0 or i == len(dates):
                print(f'  进度 {i}/{len(dates)}，新增 {added}', flush=True)
    print(f'✅ 完成：新增 {added} 条')
    for c in TARGET:
        print(f'{c:20s} 本地现有 {len(have[c])} 条')


if __name__ == '__main__':
    main()
