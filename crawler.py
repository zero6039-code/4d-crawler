import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import re

# 目标URL
URL = "https://4d4d.co/"

# 定义需要提取的公司及其在页面中对应的标识
COMPANY_CONFIG = {
    "damacai": {"table_class": "resultdamacailable", "name": "Damacai 4D"},
    "magnum": {"table_class": "resultm4dlable", "name": "Magnum 4D"},
    "toto": {"table_class": "resulttotolable", "name": "Toto 4D"},
    "singapore": {"table_class": "resultsabahlable", "name": "Singapore 4D"},
    "damacai_1p3d": {"table_class": "resultdamacailable", "name": "Da Ma Cai 1+3D"},
    "sandakan": {"table_class": "resultstc4dlable", "name": "Sandakan 4D"},
    "sarawak_cashsweep": {"table_class": "resultsteclable", "name": "Cashweep 4D"},
    "sabah": {"table_class": "resultsabahlable", "name": "Sabah88 4D"},
    "sabah_lotto": {"table_class": "resultsabahlable", "name": "Sabah Lotto"},
    "sportstoto_fireball": {"table_class": "resulttotolable", "name": "SportsToto Fireball"},
    "grand_dragon": {"table_class": "resultdamacailable", "name": "Grand Dragon"},
    "singapore_toto": {"table_class": "resultsabahlable", "name": "Singapore Toto"},
    "sportstoto_lotto": {"table_class": "resulttotolable", "name": "SportsToto Lotto"},
    "magnum_jackpot_gold": {"table_class": "resultm4dlable", "name": "Magnum Jackpot Gold"},
    "sportstoto_5d": {"table_class": "resulttotolable", "name": "SportsToto 5D"},
    "sportstoto_6d": {"table_class": "resulttotolable", "name": "SportsToto 6D"},
    "magnum_life": {"table_class": "resultm4dlable", "name": "Magnum Life"},
}

def fetch_html():
    """获取页面HTML"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        r = requests.get(URL, headers=headers, timeout=15)
        r.encoding = "utf-8"
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"❌ 抓取失败: {e}")
        return None

def extract_company_data(soup, company_key):
    """根据公司标识从soup中提取数据"""
    config = COMPANY_CONFIG[company_key]
    outer_boxes = soup.find_all("div", class_="outerbox")
    for box in outer_boxes:
        name_td = box.find("td", class_=config["table_class"])
        if name_td and config["name"] in name_td.get_text():
            return parse_outerbox(box, company_key)
    return None

def parse_outerbox(box, company_key):
    """解析单个outerbox内的数据"""
    data = {
        "draw_date": "",
        "draw_no": "",
        "1st": "",
        "2nd": "",
        "3rd": "",
        "special": [],
        "consolation": [],
        "type": None
    }

    # 提取开奖日期和期号
    draw_row = box.find("td", class_="resultdrawdate")
    if draw_row:
        date_text = draw_row.get_text(strip=True)
        match = re.search(r"(\d{2}-\d{2}-\d{4})", date_text)
        if match:
            data["draw_date"] = match.group(1)
        next_td = draw_row.find_next("td", class_="resultdrawdate")
        if next_td:
            data["draw_no"] = next_td.get_text(strip=True).replace("Draw No:", "").strip()

    # 提取前三名
    prize_tds = box.find_all("td", class_="resulttop")
    if len(prize_tds) >= 3:
        data["1st"] = prize_tds[0].get_text(strip=True)
        data["2nd"] = prize_tds[1].get_text(strip=True)
        data["3rd"] = prize_tds[2].get_text(strip=True)

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

    # 特殊公司类型标记
    if company_key in ["sportstoto_5d", "sportstoto_6d", "sportstoto_lotto", "singapore_toto", "magnum_jackpot_gold", "magnum_life"]:
        data["type"] = company_key

    return data

def save_json(company, data):
    """将数据保存为最新文件，并归档到日期子目录"""
    if not data:
        return

    base_dir = "docs/data"
    os.makedirs(base_dir, exist_ok=True)

    # 1. 保存最新文件（覆盖）
    latest_path = os.path.join(base_dir, f"{company}.json")
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已更新最新文件: {latest_path}")

    # 2. 获取开奖日期（用于归档目录）
    draw_date = data.get("draw_date", "")
    if not draw_date or draw_date == "----":
        draw_date = datetime.now().strftime("%Y-%m-%d")
    else:
        try:
            # 假设 draw_date 格式为 DD-MM-YYYY
            d = datetime.strptime(draw_date, "%d-%m-%Y")
            draw_date = d.strftime("%Y-%m-%d")
        except:
            draw_date = datetime.now().strftime("%Y-%m-%d")

    # 3. 归档到日期目录
    archive_dir = os.path.join(base_dir, draw_date)
    os.makedirs(archive_dir, exist_ok=True)
    archive_path = os.path.join(archive_dir, f"{company}.json")
    with open(archive_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"📁 已归档至: {archive_path}")

def update_dates_index():
    """更新 dates.json 索引文件，列出所有归档日期目录"""
    base_dir = "docs/data"
    if not os.path.exists(base_dir):
        return
    dates = []
    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        if os.path.isdir(item_path) and re.match(r"\d{4}-\d{2}-\d{2}", item):
            dates.append(item)
    dates.sort(reverse=True)  # 最新的靠前
    index_path = os.path.join(base_dir, "dates.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(dates, f)
    print(f"📋 已更新日期索引，共 {len(dates)} 个历史日期")

def main():
    html = fetch_html()
    if not html:
        return
    soup = BeautifulSoup(html, "html.parser")

    # 从第一个公司获取全局日期（可选）
    first_company = next(iter(COMPANY_CONFIG))
    first_data = extract_company_data(soup, first_company)
    if first_data:
        global_date = first_data["draw_date"]
        global_draw_no = first_data["draw_no"]
        with open("docs/data/latest.json", "w", encoding="utf-8") as f:
            json.dump({"draw_date": global_date, "draw_no": global_draw_no}, f)

    # 逐个提取并保存
    for company in COMPANY_CONFIG:
        data = extract_company_data(soup, company)
        save_json(company, data)

    # 最后更新日期索引
    update_dates_index()

if __name__ == "__main__":
    main()
