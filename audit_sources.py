#!/usr/bin/env python3
"""只读审计：本地 archive + GitHub + 4d4d.co + 4dlivetoday 的公司/日期覆盖。"""
import json, os, re, time
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ARCHIVE = 'docs/data/archive'
GH = {
    'magnum': 'magnum.json', 'toto': 'toto.json',
    'damacai': 'damacai.json', 'singapore': 'singapore.json',
}
GH_BASE = 'https://raw.githubusercontent.com/Senekalata/4dresulthub/main/data/'
NUM_SAMPLES = ['0000', '1234', '5678', '9999', '0520', '7777']
OP_MAP = {
    'cashsweep': 'sarawak_cashsweep', 'damacai': 'damacai',
    'gd': 'grand_dragon', 'magnum': 'magnum', 'sabah88': 'sabah',
    'sg': 'singapore', 'stc': 'sandakan', 'toto': 'toto',
}
ALL = ['sabah', 'sarawak_cashsweep', 'sandakan', 'lucky_hari', 'perdana4d',
       'grand_dragon', 'singapore', 'damacai', 'magnum', 'toto']
FOUR4D_OPS = [
    ('sabah', 'sabah88'), ('sarawak_cashsweep', 'sarawak'),
    ('sandakan', 'sandakan'), ('singapore', 'singapore'),
    ('magnum', 'magnum'), ('damacai', 'da ma cai'), ('toto', 'sports toto'),
]


def get(url, timeout=30, tries=4):
    for i in range(tries):
        try:
            req = Request(url, headers={'User-Agent': '4d-crawler-audit/1.0'})
            with urlopen(req, timeout=timeout) as r:
                return r.read().decode('utf-8', 'replace')
        except HTTPError as e:
            if e.code == 429 and i < tries - 1:
                time.sleep(5 * (i + 1))
                continue
            raise
        except Exception:
            if i < tries - 1:
                time.sleep(2)
                continue
            raise
    raise RuntimeError('unreachable')


def local_cover():
    out = {}
    for name in sorted(os.listdir(ARCHIVE)):
        if not re.fullmatch(r'\d{4}-\d{2}\.json', name):
            continue
        with open(os.path.join(ARCHIVE, name), encoding='utf-8') as f:
            month = json.load(f)
        for ymd, cs in month.items():
            for c in cs:
                s = out.setdefault(c, [ymd, ymd, 0])
                if ymd < s[0]: s[0] = ymd
                if ymd > s[1]: s[1] = ymd
                s[2] += 1
    return out


def github_cover():
    out = {}
    for c, name in GH.items():
        try:
            rows = json.loads(get(GH_BASE + name))
            dates = [str(x.get('date', ''))[:10] for x in rows if x.get('date')]
            dates = [d for d in dates if re.fullmatch(r'\d{4}-\d{2}-\d{2}', d)]
            if dates:
                out[c] = (min(dates), max(dates), len(dates))
        except Exception as e:
            print(f'  ! GitHub {name}: {type(e).__name__}')
    return out


def four4d_cover():
    try:
        t = get('https://4d4d.co/sitemap.xml')
        ds = []
        for m in re.finditer(r'/result/(\d{2})-(\d{2})-(\d{4})\.html', t):
            d, mo, y = m.groups()
            ds.append(f'{y}-{mo}-{d}')
        ds = sorted(set(ds))
        if not ds:
            print('  ! 4d4d.co: sitemap 无日期')
            return None
        day = ds[-1]
        dd, mm, yy = day.split('-')
        page = get(f'https://4d4d.co/result/{dd}-{mm}-{yy}.html').lower()
        ops = [c for c, pat in FOUR4D_OPS if pat in page]
        return ds[0], ds[-1], len(ds), ops
    except Exception as e:
        print(f'  ! 4d4d.co: {type(e).__name__}')
        return None


def api_cover():
    mins, seen = {}, {}
    for n in NUM_SAMPLES:
        try:
            j = json.loads(get('https://4dlivetoday.com/api/v1/numbers/' + n))
            for x in j.get('data', {}).get('results', []):
                c = OP_MAP.get(x.get('operator'))
                d = str(x.get('date', ''))[:10]
                if not c or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', d):
                    continue
                if c not in mins or d < mins[c]: mins[c] = d
                seen[c] = seen.get(c, 0) + 1
        except Exception as e:
            print(f'  ! 4dlivetoday {n}: {type(e).__name__}')
        time.sleep(0.8)
    return mins, seen


def main():
    print('扫描本地 archive…')
    loc = local_cover()
    print('探测外部源（只读，约 15 秒）…')
    gh = github_cover()
    f4 = four4d_cover()
    api, hits = api_cover()

    print('\n=== 本地 archive ===')
    print('公司 | 条数 | 最早 | 最新')
    for c in ALL:
        if c in loc:
            a, b, n = loc[c]
            print(f'{c:20s} | {n:6d} | {a} | {b}')
        else:
            print(f'{c:20s} |      0 | - | -')

    print('\n=== 外部源 ===')
    print('源 | 公司 | 最早 | 最新/天数 | 备注')
    for c in sorted(gh):
        a, b, n = gh[c]
        print(f'4dresulthub         | {c:20s} | {a} | {b} | {n} 期')
    if f4:
        a, b, n, ops = f4
        print(f'4d4d.co             | {",".join(ops):20s} | {a} | {b} | {n} 天')
    for c in sorted(api):
        print(f'4dlivetoday(抽检)   | {c:20s} | {api[c]} | - | {hits[c]} 次命中')
    if not api:
        print('4dlivetoday         | - | 429 或被拦截，稍后重试')

    print('\n=== 结论：可追溯最早日期（取外部源最小）===')
    for c in ALL:
        cand = []
        if c in gh: cand.append((gh[c][0], '4dresulthub'))
        if f4 and c in f4[3]: cand.append((f4[0], '4d4d.co'))
        if c in api: cand.append((api[c], '4dlivetoday'))
        if cand:
            d, src = min(cand)
            print(f'{c:20s} {d}  ({src})')
        else:
            print(f'{c:20s} 未发现外部源')


if __name__ == '__main__':
    main()
