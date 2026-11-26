#!/usr/bin/env python3
"""按年份倒序补 singapore 2008-2022；只补缺失的周三/六/日，可中断续传。"""
import os, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta

import requests
import check_local_gaps as cg
from crawler_utils import save_json

WORKERS = int(os.getenv('SG_WORKERS', '1'))
DELAY = float(os.getenv('SG_DELAY', '1.0'))
START_YEAR = int(os.getenv('SG_START', '2022'))
END_YEAR = int(os.getenv('SG_END', '2008'))
WEEKDAYS = (2, 5, 6)


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


def main():
    have = cg.load()
    sg = set(have.get('singapore', []))
    total = 0
    for y in range(START_YEAR, END_YEAR - 1, -1):
        dates = []
        d = date(y, 1, 1)
        end = date(y, 12, 31)
        while d <= end:
            s = d.isoformat()
            if d.weekday() in WEEKDAYS and s not in sg:
                dates.append(s)
            d += timedelta(days=1)
        dates.reverse()
        print(f'\n--- {y}: {len(dates)} 天待抓 ---', flush=True)
        added = 0
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futs = [ex.submit(fetch, d) for d in dates]
            for i, fut in enumerate(as_completed(futs), 1):
                ymd, results = fut.result()
                for item in results:
                    if item.get('operator') != 'sg':
                        continue
                    one, two, three = (num(item.get(k)) for k in ('first', 'second', 'third'))
                    if not (one and two and three):
                        continue
                    save_json('singapore', {
                        'draw_date': ymd, 'draw_no': item.get('draw_no', ''),
                        '1st': one, '2nd': two, '3rd': three,
                        'special': [x for x in (item.get('special') or []) if num(x)],
                        'consolation': [x for x in (item.get('consolation') or []) if num(x)],
                    })
                    sg.add(ymd)
                    added += 1
                if i % 50 == 0 or i == len(dates):
                    print(f'  进度 {i}/{len(dates)}，新增 {added}', flush=True)
                time.sleep(DELAY)
        total += added
        print(f'  {y} 完成：新增 {added}', flush=True)
    print(f'\n✅ 全部完成：新增 {total} 条', flush=True)


if __name__ == '__main__':
    main()
