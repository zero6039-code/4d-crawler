#!/usr/bin/env python3
"""按年份从近到远，只抓 gaps_three.json 里确认有缺失的年份。"""
import json, os, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import check_local_gaps as cg
from crawler_utils import save_json

TARGET = ['damacai', 'toto', 'magnum']
OP = {'magnum': 'magnum', 'toto': 'toto', 'damacai': 'damacai'}
WORKERS = int(os.getenv('GAP_WORKERS', '2'))
DELAY = float(os.getenv('GAP_DELAY', '0.4'))


def num(v):
    v = str(v or '').strip()
    return v if re.fullmatch(r'\d{4}', v) else None


def fetch(ymd):
    for attempt in range(5):
        try:
            r = requests.get('https://4dlivetoday.com/api/v1/results/' + ymd,
                             timeout=15, headers={'User-Agent': '4d-crawler/2.0'})
            r.raise_for_status()
            return ymd, r.json().get('data', {}).get('results', [])
        except Exception as e:
            if '429' in str(e):
                wait = 20 * (attempt + 1)
                print(f'  ⏳ 429 {ymd} 等 {wait}s', flush=True)
                if attempt < 4:
                    time.sleep(wait)
                    continue
            return ymd, []
    return ymd, []


def main():
    have = cg.load()
    with open('gaps_three.json', encoding='utf-8') as f:
        gaps = json.load(f)
    total_added = 0
    for c in TARGET:
        years = sorted((int(y) for y, n in gaps[c]['by_year'].items() if n > 0), reverse=True)
        pool = set(gaps[c]['missing']) | set(gaps[c]['special_candidates'])
        print(f'\n=== {c} 缺失年份（近→远）: {years} ===', flush=True)
        for y in years:
            dates = sorted((d for d in pool if d.startswith(str(y)) and d not in have[c]),
                           reverse=True)
            if not dates:
                continue
            print(f'--- {y}: {len(dates)} 天待抓 ---', flush=True)
            added = 0
            with ThreadPoolExecutor(max_workers=WORKERS) as ex:
                futs = [ex.submit(fetch, d) for d in dates]
                for i, fut in enumerate(as_completed(futs), 1):
                    ymd, results = fut.result()
                    for item in results:
                        if item.get('operator') != OP[c]:
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
                    time.sleep(DELAY)
            total_added += added
            print(f'  {y} 完成：新增 {added}', flush=True)
    print(f'\n✅ 全部完成：新增 {total_added} 条', flush=True)
    for c in TARGET:
        print(f'{c:20s} 本地现有 {len(have[c])} 条', flush=True)


if __name__ == '__main__':
    main()
