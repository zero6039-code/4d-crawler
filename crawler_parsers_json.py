import json
import re
import time
from datetime import datetime, timezone, timedelta
from crawler_http import URL_DATO4D, fetch_html, dmy_to_ymd
from crawler_storage import save_json

# ================== 从 dato4d.com JSON 批量获取所有公司数据 ==================
def extract_date_from_dd(dd_str):
    """从 DD 字段提取纯日期 (dd-mm-yyyy)"""
    if not dd_str:
        return ""
    match = re.search(r"(\d{2}-\d{2}-\d{4})", dd_str)
    return match.group(1) if match else ""

# ---------- JSON 数据提取辅助函数 ----------
def extract_standard_4d_from_json(item, company):
    """提取标准 4D 公司数据（包含 1st,2nd,3rd,special,consolation）"""
    result = {
        "draw_date": extract_date_from_dd(item.get("DD", "")),
        "draw_no": item.get("DN", ""),
        "1st": item.get("P1", ""),
        "2nd": item.get("P2", ""),
        "3rd": item.get("P3", ""),
        "special": [],
        "consolation": []
    }

    # 提取 Special (S1-S13)
    for i in range(1, 14):
        key = f"S{i}"
        if key in item:
            num = item[key]
            if num and num not in ["----", "-"]:
                result["special"].append(num)

    # 提取 Consolation (C1-C10)
    for i in range(1, 11):
        key = f"C{i}"
        if key in item:
            num = item[key]
            if num and num not in ["----", "-"]:
                result["consolation"].append(num)

    return result

def extract_magnum_from_json(item, company):
    """提取 Magnum 数据（可能包含 Life 信息，但暂时只取标准 4D）"""
    result = extract_standard_4d_from_json(item, company)
    return result

def extract_damacai_1p3d_from_json(item, company):
    """提取 Damacai 1+3D 数据"""
    result = {
        "draw_date": extract_date_from_dd(item.get("DD", "")),
        "draw_no": item.get("DN", ""),
        "1st": item.get("P1", ""),
        "2nd": item.get("P2", ""),
        "3rd": item.get("P3", ""),
        "special": [],
        "consolation": []
    }

    for i in range(1, 14):
        key = f"S{i}"
        if key in item:
            num = item[key]
            if num and num != "----":
                result["special"].append(num)
    for i in range(1, 11):
        key = f"C{i}"
        if key in item:
            num = item[key]
            if num and num != "----":
                result["consolation"].append(num)
    return result

def extract_sabah_from_json(item, company):
    """提取 Sabah 88 4D 数据（包含 3D）"""
    result = extract_standard_4d_from_json(item, company)
    result['3d'] = {
        "1st": item.get("P13D", ""),
        "2nd": item.get("P23D", ""),
        "3rd": item.get("P33D", "")
    }
    return result

def extract_grand_dragon_from_json(item, company):
    """提取 Grand Dragon 4D 数据"""
    result = extract_standard_4d_from_json(item, company)
    result["jackpot"] = ""
    return result

def extract_magnum_jackpot_gold_from_json(item, company):
    """提取 Magnum Jackpot Gold 数据"""
    result = {
        "draw_date": extract_date_from_dd(item.get("DD", "")),
        "draw_no": item.get("DN", ""),
        "groups": [],
        "jackpots": []
    }

    groups = []
    for i in range(1, 9):
        key = f"P{i}"
        if key in item and item[key]:
            groups.append({
                "group": str(i),
                "numbers": [item[key]]
            })
    result["groups"] = groups

    if "JP1" in item:
        result["jackpots"].append(item["JP1"])
    if "JP2" in item:
        result["jackpots"].append(item["JP2"])
    return result

def extract_sabah_lotto_from_json(item, company):
    """提取 Sabah Lotto 数据"""
    result = {
        "draw_date": extract_date_from_dd(item.get("DD", "")),
        "draw_no": item.get("DN", ""),
        "winning_numbers": [],
        "jackpot1": "",
        "jackpot2": ""
    }

    winning = []
    for i in range(1, 8):
        key = f"LT{i}"
        if key in item:
            num = item[key]
            if num:
                winning.append(num)
    result["winning_numbers"] = winning

    if "LTJP1" in item:
        result["jackpot1"] = item["LTJP1"]
    if "LTJP2" in item:
        result["jackpot2"] = item["LTJP2"]

    for g in range(1, 6):
        for i in range(1, 7):
            key = f"LT6G{g}{i}"
            if key in item:
                result[key] = item[key]
        jp_key = f"LT6G{g}JP"
        if jp_key in item:
            result[jp_key] = item[jp_key]

    for g in range(1, 9):
        for i in range(1, 6):
            key = f"LT5G{g}{i}"
            if key in item:
                result[key] = item[key]
        jp_key = f"LT5G{g}JP"
        if jp_key in item:
            result[jp_key] = item[jp_key]

    return result

def extract_singapore_toto_from_json(item, company):
    """提取 Singapore Toto 数据"""
    result = {
        "draw_date": extract_date_from_dd(item.get("DD", "")),
        "draw_no": item.get("DN", ""),
        "winning_numbers": [],
        "prize_table": []
    }

    winning = []
    for i in range(1, 8):
        key = f"P{i}"
        if key in item:
            num = item[key]
            if num:
                winning.append(num)
    result["winning_numbers"] = winning

    prize_groups = [
        {"group": "Group 1", "amount": item.get("JP1", ""), "winners": item.get("JPW1", "")},
        {"group": "Group 2", "amount": item.get("JP2", ""), "winners": item.get("JPW2", "")},
        {"group": "Group 3", "amount": item.get("JP3", ""), "winners": item.get("JPW3", "")},
        {"group": "Group 4", "amount": item.get("JP4", ""), "winners": item.get("JPW4", "")},
        {"group": "Group 5", "amount": item.get("JP5", ""), "winners": item.get("JPW5", "")},
        {"group": "Group 6", "amount": item.get("JP6", ""), "winners": item.get("JPW6", "")},
    ]
    result["prize_table"] = [[g["group"], g["amount"], g["winners"]] for g in prize_groups if g["amount"]]
    return result

# ================== 新增 JSON 提取函数 ==================
def extract_sportstoto_5d_from_json(t_item, company):
    return {
        "draw_date": extract_date_from_dd(t_item.get("DD", "")),
        "draw_no": t_item.get("DN", ""),
        "type": "5d",
        "1st": t_item.get("P5D1", ""),
        "2nd": t_item.get("P5D2", ""),
        "3rd": t_item.get("P5D3", ""),
        "4th": t_item.get("P5D4", ""),
        "5th": t_item.get("P5D5", ""),
        "6th": t_item.get("P5D6", "")
    }

def extract_sportstoto_6d_from_json(t_item, company):
    return {
        "draw_date": extract_date_from_dd(t_item.get("DD", "")),
        "draw_no": t_item.get("DN", ""),
        "type": "6d",
        "1st": t_item.get("P6D1", ""),
        "2nd": {
            "main": t_item.get("P6D2A", ""),
            "alt": t_item.get("P6D2B", "")
        },
        "3rd": {
            "main": t_item.get("P6D3A", ""),
            "alt": t_item.get("P6D3B", "")
        },
        "4th": {
            "main": t_item.get("P6D4A", ""),
            "alt": t_item.get("P6D4B", "")
        },
        "5th": {
            "main": t_item.get("P6D5A", ""),
            "alt": t_item.get("P6D5B", "")
        }
    }

def extract_sportstoto_lotto_from_json(t_item, company):
    def clean_num(val):
        return val if val and val not in ["-", "----"] else ""

    star = [clean_num(t_item.get(f"P650{i}")) for i in range(1, 7)] + [clean_num(t_item.get("P650EX"))]
    power = [clean_num(t_item.get(f"P655{i}")) for i in range(1, 7)]
    supreme = [clean_num(t_item.get(f"P658{i}")) for i in range(1, 7)]
    jackpots = [
        clean_num(t_item.get("P650JP1")), clean_num(t_item.get("P650JP2")),
        clean_num(t_item.get("P655JP")), clean_num(t_item.get("P658JP"))
    ]
    return {
        "draw_date": extract_date_from_dd(t_item.get("DD", "")),
        "draw_no": t_item.get("DN", ""),
        "type": "lotto",
        "star": [n for n in star if n],
        "power": [n for n in power if n],
        "supreme": [n for n in supreme if n],
        "jackpots": [n for n in jackpots if n]
    }

def extract_magnum_life_from_json(m_item, company):
    def clean_num(val):
        return val if val and val not in ["-", "----"] else ""

    winning = [clean_num(m_item.get(f"L{i}")) for i in range(1, 9)]
    bonus = [clean_num(m_item.get("LB1")), clean_num(m_item.get("LB2"))]
    return {
        "draw_date": extract_date_from_dd(m_item.get("DD", "")),
        "draw_no": m_item.get("DN", ""),
        "type": "life",
        "winning_numbers": [n for n in winning if n],
        "bonus_numbers": [n for n in bonus if n]
    }


def is_fresh(data, keys=("M", "D", "T")):
    """三大公司开奖日期是否等于马来西亚当天"""
    today = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
    for k in keys:
        item = data.get(k)
        if not isinstance(item, dict):
            return False
        if dmy_to_ymd(extract_date_from_dd(item.get("DD", ""))) != today:
            return False
    return True

def fetch_all_companies_from_dato4d(require_fresh=False):
    """从 https://www.dato4d.com/liveos.json 获取所有公司的数据"""
    print("🔍 正在从 dato4d.com JSON 批量获取所有公司数据...")
    url = URL_DATO4D + "?_=" + str(int(time.time()*1000))
    html = fetch_html(url)
    if not html:
        print("⚠️ 无法获取 dato4d.com JSON")
        return False

    try:
        data = json.loads(html)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        return False

    # 非手动模式：能解析不等于当天已开奖，未开奖则继续轮询
    if require_fresh and not is_fresh(data):
        print("⏳ JSON 可解析但三大公司尚无当天开奖数据，继续轮询...")
        return False

    # 定义公司映射：JSON键 -> 公司名, 数据提取函数
    company_mappings = {
        "M": ("magnum", extract_magnum_from_json),
        "D": ("damacai", extract_standard_4d_from_json),
        "D3": ("damacai_1p3d", extract_damacai_1p3d_from_json),
        "T": ("toto", extract_standard_4d_from_json),
        "S": ("singapore", extract_standard_4d_from_json),
        "ST": ("sandakan", extract_standard_4d_from_json),
        "SB": ("sabah", extract_sabah_from_json),
        "SW": ("sarawak_cashsweep", extract_standard_4d_from_json),
        "G": ("grand_dragon", extract_grand_dragon_from_json),
        "MJG": ("magnum_jackpot_gold", extract_magnum_jackpot_gold_from_json),
        "SBLT": ("sabah_lotto", extract_sabah_lotto_from_json),
        "SGT": ("singapore_toto", extract_singapore_toto_from_json),
        "P": ("perdana4d", extract_standard_4d_from_json),
        "H": ("lucky_hari", extract_standard_4d_from_json),
    }

    success_count = 0
    for key, (company, extract_func) in company_mappings.items():
        if key in data:
            company_data = extract_func(data[key], company)
            if company_data:
                save_json(company, company_data)
                success_count += 1
            else:
                print(f"⚠️ 提取 {company} 数据失败")
        else:
            print(f"⚠️ JSON 中缺少 {company} 的数据 (键 '{key}')")

    # 额外处理 T 对象中的 Sports Toto 5D/6D/Lotto
    if "T" in data:
        t_item = data["T"]
        toto_5d_data = extract_sportstoto_5d_from_json(t_item, "sportstoto_5d")
        if toto_5d_data and any(toto_5d_data.get(k) for k in ['1st','2nd','3rd','4th','5th','6th']):
            save_json("sportstoto_5d", toto_5d_data)
            success_count += 1
        toto_6d_data = extract_sportstoto_6d_from_json(t_item, "sportstoto_6d")
        if toto_6d_data and (toto_6d_data.get('1st') or any(toto_6d_data.get(k, {}).get('main') for k in ['2nd','3rd','4th','5th'])):
            save_json("sportstoto_6d", toto_6d_data)
            success_count += 1
        toto_lotto_data = extract_sportstoto_lotto_from_json(t_item, "sportstoto_lotto")
        if toto_lotto_data and (toto_lotto_data.get('star') or toto_lotto_data.get('power') or toto_lotto_data.get('supreme')):
            save_json("sportstoto_lotto", toto_lotto_data)
            success_count += 1
    else:
        print("⚠️ JSON 中缺少 T (Toto) 的数据")

    if "M" in data:
        m_item = data["M"]
        magnum_life_data = extract_magnum_life_from_json(m_item, "magnum_life")
        if magnum_life_data and magnum_life_data.get('winning_numbers'):
            save_json("magnum_life", magnum_life_data)
            success_count += 1
    else:
        print("⚠️ JSON 中缺少 M (Magnum) 的数据")


    print(f"✅ 从 JSON 成功获取 {success_count} 家公司数据")
    return True
