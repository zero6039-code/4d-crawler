import json
import os
import crawler_utils as cu
from crawler_http import SESSION
from crawler_backup import fetch_lucky_hari, scrape_singapore_toto

# ================== 新增：备用源抓取（Perdana 和 Lucky HariHari 晚间场） ==================
def fetch_backup_sources():
    """
    从备用源抓取 Perdana 和 Lucky HariHari 的晚间场数据。
    返回一个字典，包含 'perdana4d' 和 'lucky_hari'。
    """
    backup_data = {}
    print("🔄 正在从备用源抓取晚间场数据...")

    # --- 1. Perdana 4D (只取晚间场) ---
    try:
        url_perdana = "https://4dlivetoday.com/api/v1/operators/perdana?limit=3"
        res = SESSION.get(url_perdana, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        res.raise_for_status()
        if res.status_code == 200:
            json_data = res.json()            
            results = json_data.get("data", {}).get("results", [])
            for item in results:
                # 只取 operator 为 "perdana" (晚间场)，忽略 "perdana3pm"
                if item.get("operator") == "perdana":
                    backup_data["perdana4d"] = {
                        "draw_date": item.get("date", ""),
                        "draw_no": item.get("draw_no", ""),
                        "draw_time": "7:30 PM",  # 新增标记
                        "1st": item.get("first", ""),
                        "2nd": item.get("second", ""),
                        "3rd": item.get("third", ""),
                        "special": item.get("special", []),
                        "consolation": item.get("consolation", [])
                    }
                    print("✅ 从备用源获取到 Perdana 4D (晚间 7:30 PM) 数据")
                    break
    except Exception as e:
        print(f"⚠️ 备用源 Perdana 抓取失败: {e}")

    # --- 2. Lucky HariHari 4D（今天失败自动回退昨天）---
    lucky = fetch_lucky_hari(SESSION)
    if lucky:
        backup_data["lucky_hari"] = lucky
        print(f"✅ 从备用源获取到 Lucky HariHari 4D ({lucky['draw_date']} 晚间 7:30 PM) 数据")
    else:
        print("⚠️ 今天和昨天均未获取到 Lucky HariHari 数据，跳过更新")

    # --- 3. Singapore Toto（dato4d 停更时兜底）---
    try:
        with open(os.path.join("docs/data", "singapore_toto.json"), encoding="utf-8") as f:
            min_date = cu.to_ymd(json.load(f).get("draw_date"))
    except Exception:
        min_date = None
    sgt = scrape_singapore_toto(min_date=min_date)
    if sgt:
        backup_data["singapore_toto"] = sgt
        print(f"✅ 从备用源获取到 Singapore Toto ({sgt['draw_date']} Draw {sgt['draw_no']})")

    return backup_data

