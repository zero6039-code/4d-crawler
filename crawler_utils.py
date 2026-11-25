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

PLACEHOLDER_PRIZES = {"", "-", "----", "****", "******"}

def clean_prizes(value):
    if not isinstance(value, list):
        return []
    cleaned = []
    for item in value:
        if not isinstance(item, str):
            continue
        item = item.strip()
        if item and item not in PLACEHOLDER_PRIZES:
            cleaned.append(item)
    return cleaned

def is_valid_4d(d, company="default"):
    if not isinstance(d, dict):
        return False
    pat = NUM_RE.get(company, NUM_RE["default"])
    if not all(isinstance(d.get(k), str) and pat.match(d[k]) for k in ("1st", "2nd", "3rd")):
        return False
    return isinstance(d.get("special"), list) and isinstance(d.get("consolation"), list)

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

def _stored_ymd(path):
    try:
        with open(path, encoding="utf-8") as f:
            return to_ymd(json.load(f).get("draw_date"))
    except (OSError, ValueError, AttributeError):
        return None

def save_json(company, data, base="docs/data", allow_inferred_date=False):
    if company in FOUR_D and not is_valid_4d(data, company):
        print(f"❌ {company} 数据未通过校验，保留旧文件")
        return False
    ymd, inferred = resolve_date(data)
    if inferred and not allow_inferred_date:
        print(f"❌ {company} 缺少或无法解析 draw_date，拒绝猜测为今天，保留旧文件")
        return False
    data = {**data, "draw_date": to_dmy(ymd)}
    if company in FOUR_D:
        data = {**data,
                "special": clean_prizes(data.get("special")),
                "consolation": clean_prizes(data.get("consolation"))}

    root = os.path.join(base, f"{company}.json")
    prev = _stored_ymd(root)
    if prev and ymd < prev:
        print(f"⏭️ {company} 来源日期 {ymd} 早于现有 {prev}，不覆盖根文件")
        changed = False
    else:
        changed = atomic_write_json(root, data)

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
