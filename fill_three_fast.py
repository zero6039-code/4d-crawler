#!/usr/bin/env python3
"""并发补齐 magnum/toto/damacai；拉取与写入分离，避免并发写文件。"""
import re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta

import requests
import check_local_gaps as cg
from crawler_utils import save_json

TARGET = ['magnum', 'toto', 'damacai']
OP = {'magnum': 'magnum', 'toto': 'toto', 'damacai': 'damacai'}
FLOOR = {'magnum': '1986-08-14', 'toto': '1992-05-28', 'damacai': '1992-03-07'}
SKIP = [('2020-03-18', '2020-06-14'), ('2021-06-02', '2021-09-12')]
WORKERS = 8


def num(v):
    v = str(v or '').strip()
    return v if re.fullmatch(r'\d{4}', v) else None


def in_skip(s):
    return any(a <= s <= b for a, b in SKIP)


def collect(have):
    tasks = {}
    for c in TARGET:
        ds = sorted(have.get(c, []))
        if not ds:
            continue
        wdays, _ = cg.infer_rule(ds)
        segs, _, _ = cg.missing_segments(have[c], wdays)
        for a, b, _n in segs:
            d = date.fromisoformat(a)
            end = date.fromisoformat(b)
            while d <= end:
                s = d.isoformat()
                if (d.weekday() in wdays and s >= FLOOR[c] and
                        s not in have[c] and not in_skip(s)):
                    tasks.setdefault(s, set()).add(c)
                d += timedelta(days=1)
    return tasks


def fetch(ymd):
    for attempt in range(4):
        try:
            r = requests.get('https://4dlivetoday.com/api/v1/results/' + ymd,
                             timeout=15, headers={'User-Agent': '4d-crawler/2.0'})
            r.raise_for_status()
            return ymd, r.json().get('data', {}).get('results', [])
        except Exception as e:
            if '429' in str(e) and attempt < 3:
                time.sleep(8 * (attempt + 1))
                continue
            return ymd, []
    return ymd, []


def main():
    have = cg.load()
    tasks = collect(have)
    dates = sorted(tasks)
    print(f'待查 {len(dates)} 天（已过滤早期/停开段），并发 {WORKERS}')
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
        ds = sorted(have.get(c, []))
        wdays, _ = cg.infer_rule(ds)
        segs, _, _ = cg.missing_segments(have[c], wdays)
        print(f'{c:20s} 仍缺 {sum(n for _, _, n in segs)} 个开奖日')


if __name__ == '__main__':
    main()
