#!/usr/bin/env python3
"""本地核对：magnum/toto/damacai 每年已有天数 vs 缺失天数（只读）。"""
import json
from collections import Counter

import check_local_gaps as cg

TARGET = ['magnum', 'toto', 'damacai']


def main():
    have = cg.load()
    with open('gaps_three.json', encoding='utf-8') as f:
        gaps = json.load(f)
    for c in TARGET:
        ds = sorted(have.get(c, []))
        yhave = Counter(d[:4] for d in ds)
        ymiss = Counter(gaps[c]['by_year'])
        print(f'\n=== {c} 共 {len(ds)} 条，{ds[0]} → {ds[-1]} ===')
        print('年份 | 已有 | 缺失')
        for y in sorted(set(yhave) | set(ymiss)):
            print(f'{y} | {yhave[y]:5d} | {ymiss[y]:5d}')


if __name__ == '__main__':
    main()
