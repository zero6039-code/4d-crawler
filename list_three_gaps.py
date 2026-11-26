#!/usr/bin/env python3
"""列出 magnum/toto/damacai 完整缺失日期，按年统计，写入 gaps_three.json。"""
import json
from collections import Counter
from datetime import date, timedelta

import check_local_gaps as cg

TARGET = ['magnum', 'toto', 'damacai']
DAILY = {'grand_dragon', 'perdana4d', 'lucky_hari'}


def main():
    have = cg.load()
    cal = set()
    for c, s in have.items():
        if c not in DAILY:
            cal |= s
    out = {}
    for c in TARGET:
        ds = sorted(have.get(c, []))
        if not ds:
            continue
        wdays, label = cg.infer_rule(ds)
        segs, _, _ = cg.missing_segments(have[c], wdays)
        missing = []
        for a, b, _n in segs:
            d = date.fromisoformat(a)
            end = date.fromisoformat(b)
            while d <= end:
                if d.weekday() in wdays and d.isoformat() not in have[c]:
                    missing.append(d.isoformat())
                d += timedelta(days=1)
        special = sorted(d for d in cal
                         if date.fromisoformat(d).weekday() not in wdays
                         and ds[0] <= d <= ds[-1]
                         and d not in have[c])
        by_year = Counter(x[:4] for x in missing)
        out[c] = {
            'rule': label,
            'total': len(missing),
            'by_year': dict(sorted(by_year.items())),
            'missing': missing,
            'special_candidates': special,
        }
        print(f'\n=== {c} ({label}) 缺 {len(missing)} 天 ===')
        print('年份 | 缺失天数')
        for y in sorted(by_year):
            print(f'{y} | {by_year[y]}')
        print(f'连续段数: {len(segs)} | 特别开奖日候选: {len(special)}')
        print('最早 10 个:', ', '.join(missing[:10]))
        print('最近 10 个:', ', '.join(missing[-10:]))
        if special:
            print('特别日候选:', ', '.join(special[:20]))
    with open('gaps_three.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print('\n完整清单已写入 gaps_three.json')


if __name__ == '__main__':
    main()
