#!/usr/bin/env python3
"""从 archive 生成单一号码索引 docs/data/history_index.json。"""
import json, glob, os, re
from collections import defaultdict
COMPANIES = ['sabah','sarawak_cashsweep','sandakan','lucky_hari','perdana4d',
             'grand_dragon','singapore','damacai','magnum','toto']
PRIZES = ['1st','2nd','3rd','special','consolation']
pm = {p: i for i, p in enumerate(PRIZES)}
cm = {c: i for i, c in enumerate(COMPANIES)}
idx = defaultdict(list)
for f in sorted(glob.glob('docs/data/archive/*.json')):
    for ymd, cs in json.load(open(f, encoding='utf-8')).items():
        day = int(ymd.replace('-', ''))
        for c, obj in cs.items():
            if c not in cm: continue
            for p in PRIZES:
                v = obj.get(p, [])
                vals = v if isinstance(v, list) else ([v] if v else [])
                for n in vals:
                    n = str(n).strip()
                    if re.fullmatch(r'\d{4}', n):
                        idx[n].append([pm[p], day, cm[c]])
out = {k: v for k, v in sorted(idx.items())}
path = 'docs/data/history_index.json'
with open(path, 'w', encoding='utf-8') as f:
    json.dump(out, f, separators=(',', ':'))
print(f'索引 {len(out)} 个号码，{os.path.getsize(path)/1048576:.1f} MB')
