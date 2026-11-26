#!/usr/bin/env python3
# 数据源：4dlivetoday.com（CC BY 4.0，https://4dlivetoday.com/en/developers）
"""回补 2026 历史开奖到 docs/data/archive；只补缺失的 日期×公司，可重复运行续传。"""
import os, re, time, json
from datetime import datetime, timedelta, timezone
from crawler_utils import save_json, to_ymd
from crawler_http import SESSION
from crawler_backup import fetch_lucky_hari
from crawler_storage import update_dates_index, build_latest

MYT = timezone(timedelta(hours=8))
START = os.getenv('BACKFILL_START', '2016-01-01')
END = os.getenv('BACKFILL_END', (datetime.now(MYT) - timedelta(days=2)).strftime('%Y-%m-%d'))
SLEEP = float(os.getenv('BACKFILL_SLEEP', '1.2'))

OP_MAP = {
    'cashsweep': 'sarawak_cashsweep', 'gd': 'grand_dragon',
    'sabah88': 'sabah', 'stc': 'sandakan',
}
COMPANIES = list(OP_MAP.values())

def have_pairs(base='docs/data'):
    have = set()
    adir = os.path.join(base, 'archive')
    if not os.path.isdir(adir): return have
    for name in os.listdir(adir):
        if not re.fullmatch(r'\d{4}-\d{2}\.json', name): continue
        try:
            with open(os.path.join(adir, name), encoding='utf-8') as f:
                monthly = json.load(f)
        except (OSError, ValueError):
            continue
        for ymd, companies in monthly.items():
            for c in companies: have.add((ymd, c))
    return have

def dates_between(a, b):
    d, end = datetime.strptime(a, '%Y-%m-%d'), datetime.strptime(b, '%Y-%m-%d')
    while d <= end:
        yield d.strftime('%Y-%m-%d')
        d += timedelta(days=1)

def num(v):
    v = str(v or '').strip()
    return v if re.fullmatch(r'\d{4}', v) else None

def pack(ymd, one, two, three, sp, co, extra=None):
    one, two, three = num(one), num(two), num(three)
    if not (one and two and three): return None
    data = {'draw_date': ymd, '1st': one, '2nd': two, '3rd': three,
            'special': [n for n in (sp or []) if num(n)],
            'consolation': [n for n in (co or []) if num(n)]}
    if extra: data.update(extra)
    return data

def main():
    have = have_pairs()
    dates = list(dates_between(START, END))
    added = 0
    print(f'回补 {START} ~ {END}：{len(dates)} 天，已有 {len(have)} 条记录')
    for i, ymd in enumerate(dates, 1):
        if all((ymd, c) in have for c in COMPANIES): continue
        if any((ymd, c) not in have for c in COMPANIES if c != 'lucky_hari'):
            results = []
            for attempt in range(4):
                try:
                    r = SESSION.get('https://4dlivetoday.com/api/v1/results/' + ymd, timeout=25)
                    r.raise_for_status()
                    results = r.json().get('data', {}).get('results', [])
                    break
                except Exception as e:
                    if '429' in str(e) and attempt < 3:
                        wait = 30 * (attempt + 1)
                        print(f'  ⏳ {ymd} 429，等 {wait}s 重试 ({attempt+1}/3)')
                        time.sleep(wait)
                        continue
                    print(f'  ⚠️ {ymd} 4dlivetoday: {e}')
                    break
            for item in results:
                c = OP_MAP.get(item.get('operator'))
                if not c or (ymd, c) in have: continue
                data = pack(ymd, item.get('first'), item.get('second'), item.get('third'),
                            item.get('special'), item.get('consolation'),
                            {'draw_no': item.get('draw_no', '')})
                if data:
                    save_json(c, data)
                    have.add((ymd, c)); added += 1
            time.sleep(SLEEP)
        if i % 25 == 0 or i == len(dates):
            print(f'  进度 {i}/{len(dates)}，新增 {added} 条')
    update_dates_index()
    try: build_latest()
    except Exception as e: print(f'⚠️ build_latest: {e}')
    print(f'✅ 完成：新增 {added} 条')

if __name__ == '__main__':
    main()
