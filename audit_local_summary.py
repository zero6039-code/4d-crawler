#!/usr/bin/env python3
"""本地数据源总览（只读）。"""
import glob, json, os
from collections import defaultdict
from datetime import datetime

COMPANIES = [
    'sabah', 'sarawak_cashsweep', 'sandakan', 'lucky_hari', 'perdana4d',
    'grand_dragon', 'singapore', 'damacai', 'magnum', 'toto',
]

files = sorted(glob.glob('docs/data/archive/*.json'))
counts = defaultdict(set)
records = 0
for f in files:
    with open(f, encoding='utf-8') as fh:
        data = json.load(fh)
    for ymd, cs in data.items():
        records += 1
        for c in cs:
            if c in COMPANIES:
                counts[c].add(ymd)

print(f'archive 文件 {len(files)} 个，日期记录 {records} 条')
print('\n公司 | 天数 | 最早 | 最新')
for c in COMPANIES:
    ds = sorted(counts[c])
    print(f'{c:20s} | {len(ds):5d} | {ds[0] if ds else "-"} | {ds[-1] if ds else "-"}')

with open('docs/data/dates.json', encoding='utf-8') as f:
    dates = json.load(f)
print(f'\ndates.json: {len(dates)} 天')

p = 'docs/data/history_index.json'
if os.path.exists(p):
    with open(p, encoding='utf-8') as f:
        idx = json.load(f)
    print(f'history_index.json: {len(idx)} 个号码，{os.path.getsize(p)/1024/1024:.1f} MB，'
          f'更新于 {datetime.fromtimestamp(os.path.getmtime(p)):%Y-%m-%d %H:%M:%S}')
else:
    print('history_index.json: 不存在')
