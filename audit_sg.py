#!/usr/bin/env python3
"""singapore 本地排查：按年已有/星期分布/周三六日缺口，只读。"""
import json, glob
from collections import Counter
from datetime import date, timedelta

ds = set()
for f in glob.glob('docs/data/archive/*.json'):
    for d, cs in json.load(open(f, encoding='utf-8')).items():
        if 'singapore' in cs:
            ds.add(d)
ds = sorted(ds)
print(f'总数 {len(ds)}，最早 {ds[0]}，最新 {ds[-1]}')
print('\n年份 | 已有 | 星期分布(0=一..6=日) | 周三六日应有 | 按此缺口')
for y in range(int(ds[0][:4]), int(ds[-1][:4]) + 1):
    ys = [d for d in ds if d.startswith(str(y))]
    c = Counter(date.fromisoformat(d).weekday() for d in ys)
    cur = date(y, 1, 1)
    end = date(y, 12, 31)
    exp = 0
    while cur <= end:
        if cur.weekday() in (2, 5, 6):
            exp += 1
        cur += timedelta(days=1)
    print(f'{y} | {len(ys):4d} | {dict(sorted(c.items()))} | {exp} | {exp - len(ys)}')
