import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import re

# ---------- 配置 ----------
URL = "https://4d4d.co/"
URL_4DMOON = "https://www.4dmoon.com"

# ---------- 辅助函数 ----------
def find_parent_table(element):
    """从给定元素向上查找最近的 <table> 标签"""
    while element and element.name != 'table':
        element = element.parent
    return element

def parse_4dmoon_date(date_str):
    """将 04-Mar-2026 转换为 04-03-2026"""
    try:
        d = datetime.strptime(date_str.strip(), "%d-%b-%Y")
        return d.strftime("%d-%m-%Y")
    except:
        return None

def fetch_html_from_4dmoon(path="/"):
    """获取 4dmoon.com 指定路径的 HTML 内容"""
    url = f"{URL_4DMOON}{path}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.encoding = "utf-8"
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"❌ 抓取 4dmoon.com 失败 ({url}): {e}")
        return None

# ---------- 4dmoon.com 提取函数（优化版）----------
def extract_grand_dragon_4dmoon(soup):
    """提取 Grand Dragon 4D 数据"""
    print("🔍 定位 Grand Dragon 4D...")
    section = soup.find("td", string=re.compile(r"Grand\s+Dragon\s*4D", re.I))
    if not section:
        print("⚠️ 未找到 Grand Dragon 标题")
        return None
    print(f"✅ 找到标题: {section.get_text(strip=True)}")

    # 提取日期和期号（可能在父区域）
    parent_text = section.parent.get_text(" ", strip=True) if section.parent else ""
    date_match = re.search(r"(\d{2}-[A-Za-z]{3}-\d{4})", parent_text)
    draw_date = parse_4dmoon_date(date_match.group(1)) if date_match else None

    data = {
        "draw_date": draw_date or "",
        "draw_no": "",
        "1st": "",
        "2nd": "",
        "3rd": "",
        "special": [],
        "consolation": []
    }

    # 找到包含数据的表格
    table = find_parent_table(section)
    if not table:
        print("⚠️ Grand Dragon 未找到数据表格")
        return data

    # 提取前三名（通常有 resulttop 类或加粗样式）
    prize_cells = table.find_all("td", class_=re.compile(r"resulttop|prize", re.I))
    if len(prize_cells) >= 3:
        data["1st"] = prize_cells[0].get_text(strip=True)
        data["2nd"] = prize_cells[1].get_text(strip=True)
        data["3rd"] = prize_cells[2].get_text(strip=True)

    # 提取特别奖和安慰奖（根据实际页面结构调整）
    # 假设特别奖和安慰奖的标题单元格在表格内，然后找到其后的数字行
    special_header = table.find("td", string=re.compile(r"Special|特別獎", re.I))
    if special_header:
        special_row = special_header.find_parent("tr")
        if special_row:
            cells = special_row.find_all("td")[1:]  # 跳过标题单元格
            for cell in cells:
                num = cell.get_text(strip=True)
                if num and num != "----":
                    data["special"].append(num)

    cons_header = table.find("td", string=re.compile(r"Consolation|安慰獎", re.I))
    if cons_header:
        cons_row = cons_header.find_parent("tr")
        if cons_row:
            cells = cons_row.find_all("td")[1:]
            for cell in cells:
                num = cell.get_text(strip=True)
                if num and num != "----":
                    data["consolation"].append(num)

    return data

def extract_sportstoto_fireball_4dmoon(soup):
    """提取 SportsToto Fireball 数据"""
    print("🔍 定位 SportsToto Fireball...")
    section = soup.find("td", string=re.compile(r"SportsToto\s+Fireball", re.I))
    if not section:
        print("⚠️ 未找到 SportsToto Fireball 标题")
        return None
    print(f"✅ 找到标题: {section.get_text(strip=True)}")

    parent_text = section.parent.get_text(" ", strip=True) if section.parent else ""
    date_match = re.search(r"(\d{2}-[A-Za-z]{3}-\d{4})", parent_text)
    draw_date = parse_4dmoon_date(date_match.group(1)) if date_match else None
    no_match = re.search(r"#(\d+/\d+)", parent_text)
    draw_no = no_match.group(1) if no_match else ""

    data = {"draw_date": draw_date or "", "draw_no": draw_no, "data": []}
    table = find_parent_table(section)
    if not table:
        print("⚠️ Fireball 未找到数据表格")
        return data

    rows = table.find_all("tr")
    for row in rows:
        cells = row.find_all("td")
        # 过滤掉标题行（可能包含 "First Prize" 等）
        if len(cells) >= 2 and not cells[0].find("td", string=re.compile(r"Fireball", re.I)):
            data["data"].append([cells[0].get_text(strip=True), cells[1].get_text(strip=True)])
    return data

def extract_sportstoto_5d_4dmoon(soup):
    """提取 SportsToto 5D 数据"""
    print("🔍 定位 SportsToto 5D...")
    section = soup.find("td", string=re.compile(r"SportsToto\s+5D", re.I))
    if not section:
        print("⚠️ 未找到 SportsToto 5D 标题")
        return None
    print(f"✅ 找到标题: {section.get_text(strip=True)}")

    parent_text = section.parent.get_text(" ", strip=True) if section.parent else ""
    date_match = re.search(r"(\d{2}-[A-Za-z]{3}-\d{4})", parent_text)
    draw_date = parse_4dmoon_date(date_match.group(1)) if date_match else None
    no_match = re.search(r"#(\d+/\d+)", parent_text)
    draw_no = no_match.group(1) if no_match else ""

    data = {"draw_date": draw_date or "", "draw_no": draw_no, "data": []}
    table = find_parent_table(section)
    if not table:
        print("⚠️ 5D 未找到数据表格")
        return data

    rows = table.find_all("tr")
    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 2:
            # 跳过可能的标题行
            label = cells[0].get_text(strip=True)
            if not re.search(r"1st|2nd|3rd|4th|5th|6th", label, re.I):
                continue
            data["data"].append([label, cells[1].get_text(strip=True)])
    return data

def extract_sportstoto_6d_4dmoon(soup):
    """提取 SportsToto 6D 数据（包含 or 备选号码）"""
    print("🔍 定位 SportsToto 6D...")
    section = soup.find("td", string=re.compile(r"SportsToto\s+6D", re.I))
    if not section:
        print("⚠️ 未找到 SportsToto 6D 标题")
        return None
    print(f"✅ 找到标题: {section.get_text(strip=True)}")

    parent_text = section.parent.get_text(" ", strip=True) if section.parent else ""
    date_match = re.search(r"(\d{2}-[A-Za-z]{3}-\d{4})", parent_text)
    draw_date = parse_4dmoon_date(date_match.group(1)) if date_match else None
    no_match = re.search(r"#(\d+/\d+)", parent_text)
    draw_no = no_match.group(1) if no_match else ""

    data = {"draw_date": draw_date or "", "draw_no": draw_no, "data": []}
    table = find_parent_table(section)
    if not table:
        print("⚠️ 6D 未找到数据表格")
        return data

    rows = table.find_all("tr")
    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 3:
            # 6D 表格通常包含排名、主号码、一个 "or" 和备选号码
            # 提取前三个有效单元格
            values = []
            for cell in cells:
                text = cell.get_text(strip=True)
                if text and text != "or":
                    values.append(text)
            if len(values) >= 2:
                data["data"].append(values[:3])  # 最多取三个
    return data

def extract_sportstoto_lotto_4dmoon(soup):
    """提取 SportsToto Lotto (Star/Power/Supreme) 数据"""
    print("🔍 定位 SportsToto Lotto...")
    # 尝试找到 Star Toto 6/50 作为入口
    star_section = soup.find("td", string=re.compile(r"Star Toto 6/50", re.I))
    if not star_section:
        print("⚠️ 未找到 Star Toto 6/50")
        return None

    parent_text = star_section.parent.get_text(" ", strip=True) if star_section.parent else ""
    date_match = re.search(r"(\d{2}-[A-Za-z]{3}-\d{4})", parent_text)
    draw_date = parse_4dmoon_date(date_match.group(1)) if date_match else None
    no_match = re.search(r"#(\d+/\d+)", parent_text)
    draw_no = no_match.group(1) if no_match else ""

    data = {
        "draw_date": draw_date or "",
        "draw_no": draw_no,
        "star": [],
        "power": [],
        "supreme": [],
        "jackpots": []
    }

    # 提取 Star Toto
    star_table = find_parent_table(star_section)
    if star_table:
        rows = star_table.find_all("tr")
        if len(rows) >= 2:
            num_row = rows[1]
            tds = num_row.find_all("td")
            data["star"] = [td.get_text(strip=True) for td in tds if td.get_text(strip=True) not in ['+', '']]
        for row in rows[2:]:
            jp_tds = row.find_all("td", class_=re.compile(r"jp|jackpot", re.I))
            if jp_tds:
                data["jackpots"].append(jp_tds[0].get_text(strip=True))

    # 提取 Power Toto
    power_section = soup.find("td", string=re.compile(r"Power Toto 6/55", re.I))
    if power_section:
        power_table = find_parent_table(power_section)
        if power_table:
            rows = power_table.find_all("tr")
            if len(rows) >= 2:
                num_row = rows[1]
                tds = num_row.find_all("td")
                data["power"] = [td.get_text(strip=True) for td in tds]

    # 提取 Supreme Toto
    supreme_section = soup.find("td", string=re.compile(r"Supreme Toto 6/58", re.I))
    if supreme_section:
        supreme_table = find_parent_table(supreme_section)
        if supreme_table:
            rows = supreme_table.find_all("tr")
            if len(rows) >= 2:
                num_row = rows[1]
                tds = num_row.find_all("td")
                data["supreme"] = [td.get_text(strip=True) for td in tds]

    return data

def extract_magnum_jackpot_gold_4dmoon(soup):
    """提取 Magnum 4D Jackpot Gold 数据"""
    print("🔍 定位 Magnum Jackpot Gold...")
    section = soup.find("td", string=re.compile(r"4D Jackpot Estimated Amount", re.I))
    if not section:
        print("⚠️ 未找到 Magnum Jackpot Gold 标题")
        return None
    print(f"✅ 找到标题: {section.get_text(strip=True)}")

    parent_text = section.parent.get_text(" ", strip=True) if section.parent else ""
    date_match = re.search(r"(\d{2}-[A-Za-z]{3}-\d{4})", parent_text)
    draw_date = parse_4dmoon_date(date_match.group(1)) if date_match else None
    no_match = re.search(r"#(\d+/\d+)", parent_text)
    draw_no = no_match.group(1) if no_match else ""

    data = {"draw_date": draw_date or "", "draw_no": draw_no, "data": []}
    table = find_parent_table(section)
    if not table:
        print("⚠️ Jackpot Gold 未找到数据表格")
        return data

    rows = table.find_all("tr")
    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 2:
            data["data"].append([cells[0].get_text(strip=True), cells[1].get_text(strip=True)])
    return data

def extract_singapore_toto_4dmoon(soup):
    """提取 Singapore Toto 数据"""
    print("🔍 定位 Singapore Toto...")
    section = soup.find("td", string=re.compile(r"Singapore Toto", re.I))
    if not section:
        print("⚠️ 未找到 Singapore Toto 标题")
        return None
    print(f"✅ 找到标题: {section.get_text(strip=True)}")

    parent_text = section.parent.get_text(" ", strip=True) if section.parent else ""
    date_match = re.search(r"(\d{2}-[A-Za-z]{3}-\d{4})", parent_text)
    draw_date = parse_4dmoon_date(date_match.group(1)) if date_match else None
    no_match = re.search(r"#(\d+)", parent_text)
    draw_no = no_match.group(1) if no_match else ""

    data = {
        "draw_date": draw_date or "",
        "draw_no": draw_no,
        "winning_numbers": [],
        "prize_table": []
    }

    # 找到主表格（通常包含开奖号码）
    table = find_parent_table(section)
    if not table:
        print("⚠️ Singapore Toto 未找到主表格")
        return data

    # 提取开奖号码（假设在第二行）
    rows = table.find_all("tr")
    if len(rows) >= 2:
        num_row = rows[1]
        tds = num_row.find_all("td")
        for td in tds:
            text = td.get_text(strip=True)
            if text and text != '+':
                data["winning_numbers"].append(text)

    # 提取奖组表格（可能位于另一个表格中，或同一表格后续部分）
    # 尝试查找包含 "Prize Group" 的表格
    prize_section = soup.find("td", string=re.compile(r"Prize Group", re.I))
    if prize_section:
        prize_table = find_parent_table(prize_section)
        if prize_table:
            prize_rows = prize_table.find_all("tr")[1:]  # 跳过标题
            for row in prize_rows:
                cells = row.find_all("td")
                if len(cells) >= 3:
                    data["prize_table"].append([
                        cells[0].get_text(strip=True),
                        cells[1].get_text(strip=True),
                        cells[2].get_text(strip=True)
                    ])

    return data

# ---------- 保存 JSON 和索引更新（保持不变）----------
def save_json(company, data):
    if not data:
        print(f"❌ {company} 数据为空，跳过保存")
        return
    base_dir = "docs/data"
    os.makedirs(base_dir, exist_ok=True)
    latest_path = os.path.join(base_dir, f"{company}.json")
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已更新最新文件: {latest_path}")
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

# ---------- 原 4d4d.co 主流程（保持不变，省略以节省空间，请保留您之前的代码）----------
# ... 您的原有 main_4d4d, fetch_html, extract_global_date 等函数 ...

# ---------- 主流程整合 ----------
def main():
    # 先抓取 4d4d.co 的数据
    processed_from_4d4d, global_date = main_4d4d()
    if not global_date:
        global_date = datetime.now().strftime("%d-%m-%Y")

    # 再从 4dmoon.com 抓取补充数据
    print("\n🌙 正在从 4dmoon.com 抓取补充数据...")
    html_moon = fetch_html_from_4dmoon("/")
    if html_moon:
        soup_moon = BeautifulSoup(html_moon, "html.parser")

        moon_extractors = [
            ('grand_dragon', extract_grand_dragon_4dmoon),
            ('sportstoto_fireball', extract_sportstoto_fireball_4dmoon),
            ('sportstoto_5d', extract_sportstoto_5d_4dmoon),
            ('sportstoto_6d', extract_sportstoto_6d_4dmoon),
            ('sportstoto_lotto', extract_sportstoto_lotto_4dmoon),
            ('magnum_jackpot_gold', extract_magnum_jackpot_gold_4dmoon),
            ('singapore_toto', extract_singapore_toto_4dmoon),
        ]

        for company_key, extract_func in moon_extractors:
            print(f"🔍 处理 {company_key} (来自 4dmoon)...")
            try:
                data = extract_func(soup_moon)
                if data and any(v for v in data.values() if v not in ([], "", None)):
                    save_json(company_key, data)
                else:
                    print(f"⚠️ {company_key} 无有效数据")
            except Exception as e:
                print(f"❌ 处理 {company_key} 时出错: {e}")
                import traceback
                traceback.print_exc()

    update_dates_index()

if __name__ == "__main__":
    main()
