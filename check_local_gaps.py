#!/usr/bin/env python3
"""只读检查本地 archive：每家公司已有日期范围、开奖规律推断、缺失日期。"""
import json, os, re
from collections import Counter, defaultdict
from datetime import date, timedelta

ARCHIVE = 'docs/data/archive'
REPORT = 'gaps_report.json'
ALL = ['sabah', 'sarawak_cashsweep', 'sandakan', 'lucky_hari', 'perdana4d',
       'grand_dragon', 'singapore', 'damacai', 'magnum', 'toto']
WEEK = ['一', '二', '三', '四', '五', '六', '日']


def load():
    have = defaultdict(set)
    if not os.path.isdir(ARCHIVE):
        raise SystemExit(f'目录不存在: {ARCHIVE}')
    for name in sorted(os.listdir(ARCHIVE)):
        if not re.fullmatch(r'\d{4}-\d{2}\.json', name):
            continue
        with open(os.path.join(ARCHIVE, name), encoding='utf-8') as f:
            month = json.load(f)
        for ymd, cs in month.items():
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', ymd):
                continue
            for c in cs:
                have[c].add(ymd)
    return have


def infer_rule(ds):
    end = date.fromisoformat(ds[-1])
    start = end - timedelta(days=364)
    recent = [d for d in ds if d >= start.isoformat()]
    cnt = Counter(date.fromisoformat(d).weekday() for d in recent)
    total = Counter()
    cur = start
    while cur <= end:
        total[cur.weekday()] += 1
        cur += timedelta(days=1)
    hit = {w: cnt[w] / total[w] if total[w] else 0 for w in range(7)}
    wdays = tuple(sorted(w for w in range(7) if hit[w] >= 0.5))
    if not wdays:
        wdays = tuple(range(7))
    label = '每天' if len(wdays) == 7 else '周' + '/'.join(WEEK[w] for w in wdays)
    return wdays, label


def missing_segments(have_set, wdays):
    start = date.fromisoformat(min(have_set))
    end = date.fromisoformat(max(have_set))
    segs = []
    cur = None
    prev = None
    n = 0
    d = start
    while d <= end:
        s = d.isoformat()
        if d.weekday() in wdays:
            if s in have_set:
                if cur:
                    segs.append((cur, prev, n))
                    cur = None
            else:
                if cur:
                    n += 1
                    prev = s
                else:
                    cur = s
                    prev = s
                    n = 1
        d += timedelta(days=1)
    if cur:
        segs.append((cur, prev, n))
    return segs, start, end


def main():
    have = load()
    print('=== 本地 archive 检查（只读）===')
    print('公司 | 已有 | 最早 | 最新 | 规律 | 应有 | 缺失 | 覆盖率')
    report = {}
    for c in ALL:
        ds = sorted(have.get(c, []))
        if not ds:
            print(f'{c:20s} | 0 | - | - | - | 0 | 0 | -')
            continue
        wdays, label = infer_rule(ds)
        segs, start, end = missing_segments(have[c], wdays)
        candidate = 0
        cur = start
        while cur <= end:
            if cur.weekday() in wdays:
                candidate += 1
            cur += timedelta(days=1)
        special = sum(1 for s in ds if date.fromisoformat(s).weekday() not in wdays)
        expected = candidate + special
        missing = sum(n for _, _, n in segs)
        cover = 100.0 * len(ds) / expected if expected else 0.0
        print(f'{c:20s} | {len(ds):5d} | {ds[0]} | {ds[-1]} | {label:10s} | '
              f'{expected:5d} | {missing:5d} | {cover:5.1f}%')
        for a, b, n in sorted(segs, key=lambda x: -x[2])[:5]:
            span = a if a == b else f'{a} ~ {b}'
            print(f'    缺口 {span} ({n} 个开奖日)')
        report[c] = {
            'rule': label,
            'from': ds[0],
            'to': ds[-1],
            'have': len(ds),
            'expected': expected,
            'missing': missing,
            'segments': [{'from': a, 'to': b, 'draw_days': n} for a, b, n in segs],
        }
    with open(REPORT, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f'\n完整缺口分段已写入 {REPORT}')


if __name__ == '__main__':
    main()
