import json, os, re, tempfile
from datetime import datetime, timezone, timedelta

MYT = timezone(timedelta(hours=8))

def to_ymd(s):
    if not s:
        return None
    s = str(s).strip().split("T")[0].split(" ")[0]
    for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None

def to_dmy(s):
    y = to_ymd(s)
    return datetime.strptime(y, "%Y-%m-%d").strftime("%d-%m-%Y") if y else ""

NUM_RE = {
    "default": re.compile(r"^\d{4}$"),
    "damacai_1p3d": re.compile(r"^\d{3} ?\d{3}$"),
}
FOUR_D = {"magnum", "damacai", "toto", "singapore", "sandakan", "sabah",
          "sarawak_cashsweep", "grand_dragon", "perdana4d", "lucky_hari",
          "damacai_1p3d"}

def is_valid_4d(d, company="default"):
    if not isinstance(d, dict):
        return False
    pat = NUM_RE.get(company, NUM_RE["default"])
    return all(isinstance(d.get(k), str) and pat.match(d[k]) for k in ("1st", "2nd", "3rd"))

def resolve_date(d, now=None):
    ymd = to_ymd(d.get("draw_date"))
    return (ymd, False) if ymd else ((now or datetime.now(MYT)).strftime("%Y-%m-%d"), True)

def is_fresh_date(d, today=None):
    today = today or datetime.now(MYT).strftime("%Y-%m-%d")
    return to_ymd(d.get("draw_date")) == today

def atomic_write_json(path, obj):
    new = json.dumps(obj, ensure_ascii=False, indent=2)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            if f.read() == new:
                return False
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(new)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return True

def save_json(company, data, base="docs/data"):
    if company in FOUR_D and not is_valid_4d(data, company):
        print(f"❌ {company} 数据未通过校验，保留旧文件")
        return False
    ymd, inferred = resolve_date(data)
    if inferred:
        print(f"⚠️ {company} 缺少 draw_date，按今天 {ymd} 归档")
    data = {**data, "draw_date": to_dmy(ymd)}
    changed = atomic_write_json(os.path.join(base, f"{company}.json"), data)

    # 按月归档：每次成功保存写入 YYYY-MM.json 的当天键，跨月自动建新文件
    month = ymd[:7]
    archive_path = os.path.join(base, "archive", f"{month}.json")
    monthly = {}
    if os.path.exists(archive_path):
        try:
            with open(archive_path, encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                monthly = loaded
        except (OSError, ValueError):
            monthly = {}
    monthly.setdefault(ymd, {})[company] = data
    atomic_write_json(archive_path, monthly)
    return changed
