import json, os, sys
from collections import Counter
from datetime import datetime, timedelta
from crawler_utils import to_ymd, MYT

WEEKS = 26
THRESHOLD = 0.6

def expected_draw_companies(today, base="docs/data/archive", weeks=WEEKS, threshold=THRESHOLD):
    """按过去 N 周同星期命中率（≥threshold）推断今天应开奖公司；排除今天。"""
    if isinstance(today, str):
        today = datetime.strptime(today, "%Y-%m-%d").date()
    hits = Counter()
    samples = 0
    for w in range(1, weeks + 1):
        d = today - timedelta(weeks=w)
        path = os.path.join(base, f"{d:%Y-%m}.json")
        try:
            with open(path, encoding="utf-8") as f:
                monthly = json.load(f)
        except (OSError, ValueError):
            continue
        day = monthly.get(d.isoformat()) if isinstance(monthly, dict) else None
        if not isinstance(day, dict):
            continue
        samples += 1
        hits.update(c for c in day if isinstance(c, str))
    if not samples:
        return set()
    cutoff = samples * threshold
    return {c for c, n in hits.items() if n >= cutoff}

def check(base="docs/data", today=None):
    now = datetime.now(MYT)
    # Actions cron 可能延迟跨日；22:00 MYT 前数据未整合，跳过避免误报
    if today is None and now.hour < 22:
        return now.date(), set(), []
    today = today or now.date()
    expected = expected_draw_companies(today, base=os.path.join(base, "archive"))
    missing = []
    for company in sorted(expected):
        try:
            with open(os.path.join(base, f"{company}.json"), encoding="utf-8") as f:
                ymd = to_ymd(json.load(f).get("draw_date"))
        except (OSError, ValueError, AttributeError):
            ymd = None
        if ymd != today.isoformat():
            missing.append(company)
    return today, expected, missing

if __name__ == "__main__":
    today, expected, missing = check()
    print(f"{today} 预期开奖 {len(expected)} 家；缺少当天数据: {missing or '无'}")
    sys.exit(1 if missing else 0)
