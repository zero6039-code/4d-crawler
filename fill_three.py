#!/usr/bin/env python3
"""补齐 magnum / toto / damacai 的缺口；只补缺失的 日期×公司，不覆盖已有。"""
import re, time
from datetime import date, timedelta

import check_local_gaps as cg
from crawler_utils import save_json
import requests

TARGET = ['magnum', 'toto', 'damacai']
OP = {'magnum': 'magnum', 'toto': 'toto', 'damacai': 'damacai'}


def num(v):
    v = str(v or '').strip()
    return v if re.fullmatch(r'\d{4}', v) else None


def collect_tasks(have):
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
                if d.weekday() in wdays and s not in have[c]:
                    tasks.setdefault(s, set()).add(c)
                d += timedelta(days=1)
    return tasks


def main():
    have = cg.load()
    tasks = collect_tasks(have)
    print(f'待查日期 {len(tasks)} 天：')
    for c in TARGET:
        print(f'  {c}: {sum(1 for cs in tasks.values() if c in cs)} 个缺失开奖日')

    added = 0
    for i, ymd in enumerate(sorted(tasks), 1):
        results = []
        for attempt in range(4):
            try:
                r = requests.get('https://4dlivetoday.com/api/v1/results/' + ymd, timeout=15, headers={'User-Agent': '4d-crawler/2.0'})
                r.raise_for_status()
                results = r.json().get('data', {}).get('results', [])
                break
            except Exception as e:
                if '429' in str(e) and attempt < 3:
                    time.sleep(20 * (attempt + 1))
                    continue
                break
        for item in results:
            c = OP.get(item.get('operator'))
            if c not in tasks[ymd]:
                continue
            one, two, three = (num(item.get(k)) for k in ('first', 'second', 'third'))
            if not (one and two and three):
                continue
            data = {
                'draw_date': ymd,
                'draw_no': item.get('draw_no', ''),
                '1st': one, '2nd': two, '3rd': three,
                'special': [x for x in (item.get('special') or []) if num(x)],
                'consolation': [x for x in (item.get('consolation') or []) if num(x)],
            }
            save_json(c, data)
            have[c].add(ymd)
            added += 1
        if i % 5 == 0 or i == len(tasks):
            print(f'  进度 {i}/{len(tasks)} {ymd}，新增 {added} 条', flush=True)
        time.sleep(1.0)

    print(f'✅ 完成：新增 {added} 条')
    print('\n=== 补后仍缺 ===')
    for c in TARGET:
        ds = sorted(have.get(c, []))
        if not ds:
            continue
        wdays, _ = cg.infer_rule(ds)
        segs, _, _ = cg.missing_segments(have[c], wdays)
        n = sum(x[2] for x in segs)
        print(f'{c:20s} 仍缺 {n} 个开奖日')
        for a, b, k in sorted(segs, key=lambda x: -x[2])[:5]:
            span = a if a == b else f'{a} ~ {b}'
            print(f'    {span} ({k} 天)')
    print('\n刷新报告：python3 check_local_gaps.py')


if __name__ == '__main__':
    main()
