#!/usr/bin/env python3
"""本地核对 sabah/sarawak_cashsweep/sandakan 缺口，只读，写 gaps_east.json。"""
import json
from collections import Counter
from datetime import date, timedelta

import check_local_gaps as cg

TARGET = ['sabah', 'sarawak_cashsweep', 'sandakan']
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
            d, end = date.fromisoformat(a), date.fromisoformat(b)
            while d <= end:
                if d.weekday() in wdays and d.isoformat() not in have[c]:
                    missing.append(d.isoformat())
                d += timedelta(days=1)
        special = sorted(d for d in cal
                         if date.fromisoformat(d).weekday() not in wdays
                         and ds[0] <= d <= ds[-1] and d not in have[c])

        yhave, ymiss = Counter(x[:4] for x in ds), Counter(x[:4] for x in missing)
        years = sorted(set(yhave) | set(ymiss))
        out[c] = {
            'rule': label, 'total': len(ds), 'first': ds[0], 'last': ds[-1],
            'missing': missing, 'special_candidates': special,
            'by_year': {y: {'have': yhave[y], 'missing': ymiss[y]} for y in years},
        }

        print(f'\n=== {c} 共 {len(ds)} 条，{ds[0]} → {ds[-1]}（{label}）缺 {len(missing)} 天 ===')
        print('年份 | 已有 | 缺失 | 星期分布(0=一..6=日)')
        for y in years:
            wd = Counter(date.fromisoformat(x).weekday() for x in ds if x.startswith(y))
            print(f'{y} | {yhave[y]:4d} | {ymiss[y]:5d} | {dict(sorted(wd.items()))}')
        print(f'连续段 {len(segs)} | 特别开奖日候选 {len(special)}')
        if special:
            print('特别日候选:', ', '.join(special[:20]))

    with open('gaps_east.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print('\n完整清单已写入 gaps_east.json')


if __name__ == '__main__':
    main()
