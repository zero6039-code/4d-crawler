import json
import os
import re
from datetime import datetime, timezone, timedelta
from crawler_utils import save_json as _save_json

# ---------- 保存 JSON 和索引 ----------
def save_json(company, data, base="docs/data"):
    return _save_json(company, data, base)

def update_dates_index(base_dir="docs/data"):
    arch_dir = os.path.join(base_dir, "archive")
    days = set()
    if os.path.isdir(arch_dir):
        for name in os.listdir(arch_dir):
            if not re.fullmatch(r"\d{4}-\d{2}\.json", name):
                continue
            try:
                with open(os.path.join(arch_dir, name), encoding="utf-8") as f:
                    monthly = json.load(f)
            except (OSError, ValueError) as e:
                print(f"❌ 归档 {name} 无法解析 ({e!r})，中止索引更新，保留现有 dates.json")
                return False
            if isinstance(monthly, dict):
                days.update(k for k, v in monthly.items()
                            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", k) and v)
    if not days:
        print("⚠️ 归档为空，保留现有 dates.json")
        return
    ordered = sorted(days, reverse=True)
    index_path = os.path.join(base_dir, "dates.json")
    tmp = index_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(ordered, f)
    os.replace(tmp, index_path)
    print(f"📋 已更新日期索引，共 {len(ordered)} 个历史日期")

# ---------- 聚合文件（前端单请求） ----------
def _atomic_dump(obj, path):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, path)

def build_latest(base="docs/data"):
    out = {}
    if not os.path.isdir(base):
        return
    for name in sorted(os.listdir(base)):
        if not name.endswith(".json"):
            continue
        stem = name[:-5]
        if stem in ("dates", "latest", "meta", "history_index", "sportstoto_fireball") or stem.endswith("_all"):
            continue
        try:
            with open(os.path.join(base, name), encoding="utf-8") as f:
                out[stem] = json.load(f)
        except (OSError, ValueError):
            continue
    latest_path = os.path.join(base, "latest.json")
    _atomic_dump(out, latest_path)
    _write_meta(base, latest_path)


def _write_meta(base, latest_path):
    """前端 60s 轮询的版本号：latest.json + dates.json 内容变化才会变。"""
    import hashlib
    h = hashlib.sha256()
    for name in (latest_path, os.path.join(base, "dates.json")):
        try:
            with open(name, "rb") as f:
                h.update(f.read())
        except OSError:
            pass
    _atomic_dump({"rev": h.hexdigest()[:12]}, os.path.join(base, "meta.json"))



def update_sitemap(today=None):
    """抓取成功后更新 sitemap.xml 的 lastmod（内容不变则不写入）"""
    today = today or datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
    path = "docs/sitemap.xml"
    try:
        with open(path, encoding="utf-8") as f:
            s = f.read()
        updated = re.sub(r"<lastmod>.*?</lastmod>", f"<lastmod>{today}</lastmod>", s)
        if updated != s:
            with open(path, "w", encoding="utf-8") as f:
                f.write(updated)
            print(f"🗺️ 已更新 sitemap lastmod: {today}")
    except OSError as e:
        print(f"⚠️ 更新 sitemap 失败: {e}")
