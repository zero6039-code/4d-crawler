import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import re

URL = "https://4d4d.co/"

# 公司名称到 key 的映射（必须与页面显示完全一致）
COMPANY_NAME_TO_KEY = {
    "Damacai 4D": "damacai",
    "Magnum 4D": "magnum",
    "Toto 4D": "toto",
    "Singapore 4D": "singapore",
    "Da Ma Cai 1+3D": "damacai_1p3d",
    "Sandakan 4D": "sandakan",
    "Cashweep 4D": "sarawak_cashsweep",
    "Sabah88 4D": "sabah",
    "Sabah Lotto": "sabah_lotto",
    "SportsToto Fireball": "sportstoto_fireball",
    "Grand Dragon": "grand_dragon",
    "Singapore Toto": "singapore_toto",
    "SportsToto Lotto": "sportstoto_lotto",
    "Magnum Jackpot Gold": "magnum_jackpot_gold",
    "SportsToto 5D": "sportstoto_5d",
    "SportsToto 6D": "sportstoto_6d",
    "Magnum Life": "magnum_life",
}

# 显示名称（前端使用）
NAME_MAP = {
    "damacai": "DAMACAI 4D",
    "magnum": "MAGNUM 4D",
    "toto": "TOTO 4D",
    "singapore": "SINGAPORE 4D",
    "damacai_1p3d": "DAMACAI 1+3D",
    "sandakan": "SANDAKAN 4D",
    "sarawak_cashsweep": "SARAWAK CASHSWEEP",
    "sabah": "SABAH 88 4D",
    "sabah_lotto": "SABAH LOTTO",
    "sportstoto_fireball": "SPORTSTOTO FIREBALL",
    "grand_dragon": "GRAND DRAGON",
    "singapore_toto": "SINGAPORE TOTO",
    "sportstoto_lotto": "SPORTSTOTO LOTTO",
    "magnum_jackpot_gold": "MAGNUM JACKPOT GOLD",
    "sportstoto_5d": "SPORTSTOTO 5D",
    "sportstoto_6d": "SPORTSTOTO 6D",
    "magnum_life": "MAGNUM LIFE",
}

# 需要特殊渲染的公司列表
SPECIAL_COMPANIES = [
    "sportstoto_fireball", "sportstoto_lotto", "singapore_toto",
    "magnum_jackpot_gold", "sportstoto_5d", "sportstoto_6d", "magnum_life"
]

def fetch_html():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(URL, headers=headers, timeout=15)
        r.encoding = "utf-8"
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"❌ 抓取失败: {e}")
        return None

def extract_global_date(soup):
    """从页面第一个 outerbox 提取全局日期和期号"""
    first_box = soup.find("div", class_="outerbox")
    if not first_box:
        return None, None
    draw_row = first_box.find("td", class_="resultdrawdate")
    if not draw_row:
        return None, None
    date_text = draw_row.get_text(strip=True)
    match = re.search(r"(\d{2}-\d{2}-\d{4})", date_text)
    date = match.group(1) if match else None
    next_td = draw_row.find_next("td", class_="resultdrawdate")
    draw_no = None
    if next_td:
        no_text = next_td.get_text(strip=True)
        draw_no = re.sub(r"Draw No:?", "", no_text).strip()
    return date, draw_no

def parse_outerbox(box, global_date, global_draw_no):
    """解析单个 outerbox，返回 (company_key, data)"""
    # 尝试从多种方式获取公司名称
    company_name = None

    # 方法1：查找可能包含公司名的 td
    possible_classes = ["resultdamacailable", "resultm4dlable", "resulttotolable", "resultsabahlable", "resultstc4dlable", "resultsteclable"]
    for cls in possible_classes:
        name_td = box.find("td", class_=cls)
        if name_td:
            text = name_td.get_text(strip=True)
            if text and not text.startswith(("img", "http")):
                company_name = text
                break

    # 方法2：从图片 alt 属性获取
    if not company_name:
        img = box.find("img")
        if img and img.get("alt"):
            company_name = img["alt"]

    if not company_name:
        print("⚠️ 无法识别公司名称")
        return None, None

    company_key = COMPANY_NAME_TO_KEY.get(company_name)
    if not company_key:
        print(f"⚠️ 未知公司名称: {company_name}")
        return None, None

    data = {
        "draw_date": "",
        "draw_no": "",
        "1st": "",
        "2nd": "",
        "3rd": "",
        "special": [],
        "consolation": [],
        "type": company_key if company_key in SPECIAL_COMPANIES else None
    }

    # 提取自己的日期和期号
    draw_row = box.find("td", class_="resultdrawdate")
    if draw_row:
        date_text = draw_row.get_text(strip=True)
        match = re.search(r"(\d{2}-\d{2}-\d{4})", date_text)
        if match:
            data["draw_date"] = match.group(1)
        next_td = draw_row.find_next("td", class_="resultdrawdate")
        if next_td:
            no_text = next_td.get_text(strip=True)
            data["draw_no"] = re.sub(r"Draw No:?", "", no_text).strip()

    # 如果没有自己的日期，使用全局日期
    if not data["draw_date"] and global_date:
        data["draw_date"] = global_date
    if not data["draw_no"] and global_draw_no:
        data["draw_no"] = global_draw_no

    # 前三名
    prize_tds = box.find_all("td", class_="resulttop")
    if len(prize_tds) >= 3:
        data["1st"] = prize_tds[0].get_text(strip=True)
        data["2nd"] = prize_tds[1].get_text(strip=True)
        data["3rd"] = prize_tds[2].get_text(strip=True)
    else:
        print(f"⚠️ {company_key} 未找到前三名")

    # 特别奖
    special_section = box.find("td", string=re.compile("Special|特別獎"))
    if special_section:
        table = special_section.find_parent("table")
        if table:
            rows = table.find_all("tr")
            special_numbers = []
            for row in rows[1:]:
                tds = row.find_all("td", class_="resultbottom")
                for td in tds:
                    num = td.get_text(strip=True)
                    if num and num != "----":
                        special_numbers.append(num)
            data["special"] = special_numbers

    # 安慰奖
    cons_section = box.find("td", string=re.compile("Consolation|安慰獎"))
    if cons_section:
        table = cons_section.find_parent("table")
        if table:
            rows = table.find_all("tr")
            cons_numbers = []
            for row in rows[1:]:
                tds = row.find_all("td", class_="resultbottom")
                for td in tds:
                    num = td.get_text(strip=True)
                    if num and num != "----":
                        cons_numbers.append(num)
            data["consolation"] = cons_numbers

    return company_key, data

def save_json(company, data):
    if not data:
        print(f"❌ {company} 数据为空，跳过保存")
        return
    base_dir = "docs/data"
    os.makedirs(base_dir, exist_ok=True)

    # 最新文件
    latest_path = os.path.join(base_dir, f"{company}.json")
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已更新最新文件: {latest_path}")

    # 归档
    draw_date = data.get("draw_date", "")
    if not draw_date or draw_date == "----":
        draw_date = datetime.now().strftime("%Y-%m-%d")
    else:
        try:
            d = datetime.strptime(draw_date, "%d-%m-%Y")
            draw_date = d.strftime("%Y-%m-%d")
        except:
            draw_date = datetime.now().strftime("%Y-%m-%d")

    archive_dir = os.path.join(base_dir, draw_date)
    os.makedirs(archive_dir, exist_ok=True)
    archive_path = os.path.join(archive_dir, f"{company}.json")
    with open(archive_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"📁 已归档至: {archive_path}")

def update_dates_index():
    base_dir = "docs/data"
    if not os.path.exists(base_dir):
        return
    dates = []
    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        if os.path.isdir(item_path) and re.match(r"\d{4}-\d{2}-\d{2}", item):
            dates.append(item)
    dates.sort(reverse=True)
    index_path = os.path.join(base_dir, "dates.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(dates, f)
    print(f"📋 已更新日期索引，共 {len(dates)} 个历史日期")

def main():
    html = fetch_html()
    if not html:
        return
    soup = BeautifulSoup(html, "html.parser")

    global_date, global_draw_no = extract_global_date(soup)
    print(f"🌍 全局日期: {global_date}, 全局期号: {global_draw_no}")

    outer_boxes = soup.find_all("div", class_="outerbox")
    print(f"📦 找到 {len(outer_boxes)} 个 outerbox")

    processed_keys = set()

    for idx, box in enumerate(outer_boxes):
        print(f"🔍 正在解析第 {idx+1} 个 outerbox...")
        company_key, data = parse_outerbox(box, global_date, global_draw_no)
        if company_key and data:
            if company_key in processed_keys:
                print(f"⚠️ 重复的公司 {company_key}，跳过")
                continue
            save_json(company_key, data)
            processed_keys.add(company_key)
        else:
            print(f"⚠️ 第 {idx+1} 个 outerbox 解析失败")

    # 检查遗漏
    all_keys = set(COMPANY_NAME_TO_KEY.values())
    missing = all_keys - processed_keys
    if missing:
        print(f"❌ 以下公司未找到: {missing}")
    else:
        print("✅ 所有公司均已成功处理")

    update_dates_index()

if __name__ == "__main__":
    main()
