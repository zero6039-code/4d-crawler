import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import re

# ---------- 配置 ----------
URL_4D4D = "https://4d4d.co/"
URL_4DMOON = "https://www.4dmoon.com"

# ---------- 辅助函数 ----------
def fetch_html(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.encoding = "utf-8"
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"❌ 抓取失败 {url}: {e}")
        return None

def find_parent_table(element):
    while element and element.name != 'table':
        element = element.parent
    return element

def parse_4dmoon_date(date_str):
    """将 02-Mar-2026 转换为 02-03-2026"""
    try:
        d = datetime.strptime(date_str.strip(), "%d-%b-%Y")
        return d.strftime("%d-%m-%Y")
    except:
        return None

def extract_global_date(soup):
    """从第一个 outerbox 中提取全局日期和期号"""
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

# ---------- 4d4d.co 提取函数 ----------
def extract_damacai(box, global_date, global_draw_no):
    return base_extract(box, global_date, global_draw_no)

def extract_magnum(box, global_date, global_draw_no):
    return base_extract(box, global_date, global_draw_no)

def extract_toto(box, global_date, global_draw_no):
    return base_extract(box, global_date, global_draw_no)

def extract_singapore(box, global_date, global_draw_no):
    data = {
        "draw_date": global_date,
        "draw_no": global_draw_no,
        "1st": "",
        "2nd": "",
        "3rd": "",
        "special": [],
        "consolation": [],
        "type": None
    }
    prize_tds = box.find_all("td", class_="resulttop")
    if len(prize_tds) >= 3:
        data["1st"] = prize_tds[0].get_text(strip=True)
        data["2nd"] = prize_tds[1].get_text(strip=True)
        data["3rd"] = prize_tds[2].get_text(strip=True)

    def extract_numbers_from_section(title_pattern):
        section = box.find("td", string=re.compile(title_pattern))
        if not section:
            return []
        table = section.find_parent("table")
        if not table:
            return []
        rows = table.find_all("tr")[1:]
        numbers = []
        for row in rows:
            cells = row.find_all("td")
            for cell in cells:
                text = cell.get_text(strip=True)
                if text and text not in ["Special", "特別獎", "Consolation", "安慰獎", "----"]:
                    numbers.append(text)
        return numbers

    data["special"] = extract_numbers_from_section("Special|特別獎")
    data["consolation"] = extract_numbers_from_section("Consolation|安慰獎")
    return data

def extract_damacai_1p3d(box, global_date, global_draw_no):
    return base_extract(box, global_date, global_draw_no)

def extract_sandakan(box, global_date, global_draw_no):
    return base_extract(box, global_date, global_draw_no)

def extract_cashsweep(box, global_date, global_draw_no):
    return base_extract(box, global_date, global_draw_no)

def extract_sabah(box, global_date, global_draw_no):
    data = base_extract(box, global_date, global_draw_no)
    data['3d'] = extract_3d(box)
    return data

def extract_sportstoto_5d(box, global_date, global_draw_no):
    data = base_extract(box, global_date, global_draw_no)
    data['type'] = '5d_table'
    data['data'] = extract_5d_table(box)
    return data

def extract_sportstoto_6d(box, global_date, global_draw_no):
    data = base_extract(box, global_date, global_draw_no)
    data['type'] = '6d_table'
    data['data'] = extract_6d_table(box)
    return data

def extract_sportstoto_lotto(box, global_date, global_draw_no):
    data = base_extract(box, global_date, global_draw_no)
    data['type'] = 'lotto'
    data['star'], data['power'], data['supreme'], data['jackpots'] = extract_lotto(box)
    return data

def extract_grand_dragon(box, global_date, global_draw_no):
    return base_extract(box, global_date, global_draw_no)

def base_extract(box, global_date, global_draw_no):
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
    if not data["draw_date"] and global_date:
        data["draw_date"] = global_date
    if not data["draw_no"] and global_draw_no:
        data["draw_no"] = global_draw_no
    prize_tds = box.find_all("td", class_="resulttop")
    if len(prize_tds) >= 3:
        data["1st"] = prize_tds[0].get_text(strip=True)
        data["2nd"] = prize_tds[1].get_text(strip=True)
        data["3rd"] = prize_tds[2].get_text(strip=True)
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
    return data

def extract_3d(box):
    h3 = box.find("td", string=re.compile("3D"))
    if not h3:
        return {}
    table = h3.find_parent("table")
    if not table:
        return {}
    prize_tds = table.find_all("td", class_="resulttop")
    if len(prize_tds) >= 3:
        return {
            "1st": prize_tds[0].get_text(strip=True),
            "2nd": prize_tds[1].get_text(strip=True),
            "3rd": prize_tds[2].get_text(strip=True)
        }
    return {}

def extract_5d_table(box):
    h5 = box.find("td", string=re.compile(r"5D"))
    if not h5:
        return []
    table = h5.find_parent("table")
    if not table:
        return []
    rows = table.find_all("tr")
    data = []
    for row in rows:
        tds = row.find_all("td")
        if len(tds) < 2:
            continue
        cells_text = [td.get_text(strip=True) for td in tds if td.get_text(strip=True)]
        for i in range(0, len(cells_text), 2):
            if i+1 < len(cells_text):
                label = cells_text[i]
                number = cells_text[i+1]
                if label not in ["5D", "6D", "SportsToto"] and number:
                    data.append([label, number])
    return data

def extract_6d_table(box):
    h6 = box.find("td", string=re.compile(r"6D"))
    if not h6:
        return []
    table = h6.find_parent("table")
    if not table:
        return []
    rows = table.find_all("tr")
    data = []
    for row in rows:
        tds = row.find_all("td")
        if len(tds) < 2:
            continue
        cells_text = [td.get_text(strip=True) for td in tds if td.get_text(strip=True) and td.get_text(strip=True).lower() != "or"]
        if len(cells_text) >= 2:
            rank = cells_text[0]
            main_num = cells_text[1]
            alt_num = cells_text[2] if len(cells_text) >= 3 else ""
            if rank not in ["6D", "SportsToto"]:
                data.append([rank, main_num, alt_num])
        elif len(tds) >= 2:
            rank = tds[0].get_text(strip=True)
            main_num = tds[1].get_text(strip=True)
            if rank not in ["6D", "SportsToto"]:
                data.append([rank, main_num, ""])
    return data

def extract_lotto(box):
    star = []
    power = []
    supreme = []
    jackpots = []
    star_section = box.find("td", string=re.compile("Star Toto 6/50"))
    if star_section:
        table = star_section.find_parent("table")
        if table:
            rows = table.find_all("tr")
            if len(rows) >= 2:
                num_row = rows[1]
                tds = num_row.find_all("td", class_="resultbottomtoto2")
                star = [td.get_text(strip=True) for td in tds if td.get_text(strip=True) not in ['+', '']]
            for row in rows[2:]:
                jp_tds = row.find_all("td", class_="resultbottomtotojpval")
                if jp_tds:
                    jackpots.append(jp_tds[0].get_text(strip=True))
    power_section = box.find("td", string=re.compile("Power Toto 6/55"))
    if power_section:
        table = power_section.find_parent("table")
        if table:
            rows = table.find_all("tr")
            if len(rows) >= 2:
                num_row = rows[1]
                tds = num_row.find_all("td", class_="resultbottomtoto2")
                power = [td.get_text(strip=True) for td in tds]
            for row in rows:
                if "Jackpot" in row.get_text():
                    jp_tds = row.find_all("td")
                    for td in jp_tds:
                        text = td.get_text(strip=True)
                        if text.startswith("RM"):
                            jackpots.append(text)
                            break
                    break
    supreme_section = box.find("td", string=re.compile("Supreme Toto 6/58"))
    if supreme_section:
        table = supreme_section.find_parent("table")
        if table:
            rows = table.find_all("tr")
            if len(rows) >= 2:
                num_row = rows[1]
                tds = num_row.find_all("td", class_="resultbottomtoto2")
                supreme = [td.get_text(strip=True) for td in tds]
            for row in rows:
                if "Jackpot" in row.get_text():
                    jp_tds = row.find_all("td")
                    for td in jp_tds:
                        text = td.get_text(strip=True)
                        if text.startswith("RM"):
                            jackpots.append(text)
                            break
                    break
    return star, power, supreme, jackpots

# ---------- 从 4dmoon.com 提取 Singapore Toto ----------
def extract_singapore_toto_4dmoon(soup):
    """
    专门从 https://www.4dmoon.com/singapore-4d-results/ 的页面解析数据
    """
    print("🔍 开始解析 Singapore Toto 页面...")
    data = {
        "draw_date": "",
        "draw_no": "",
        "winning_numbers": [],
        "prize_table": []
    }

    # 1. 定位到包含 "Singapore Toto" 的单元格，这是所有数据的起点
    toto_header = soup.find("td", string=re.compile(r"Singapore Toto", re.I))
    if not toto_header:
        print("❌ 错误：未找到 'Singapore Toto' 标题")
        return None
    print(f"✅ 找到标题: {toto_header.get_text(strip=True)}")

    # 2. 提取日期和期号（通常在标题的父级区域）
    parent_cell = toto_header.find_parent("td")
    if parent_cell:
        parent_text = parent_cell.get_text(" ", strip=True)
        print(f"📅 日期区域文本: {parent_text}")

        # 匹配日期，例如 (Mon) 02-Mar-2026
        date_match = re.search(r"(\d{2}-[A-Za-z]{3}-\d{4})", parent_text)
        if date_match:
            parsed_date = parse_4dmoon_date(date_match.group(1))
            if parsed_date:
                data["draw_date"] = parsed_date
                print(f"  提取到日期: {data['draw_date']}")
        # 匹配期号，例如 #4161
        no_match = re.search(r"#(\d+)", parent_text)
        if no_match:
            data["draw_no"] = no_match.group(1)
            print(f"  提取到期号: {data['draw_no']}")

    # 3. 提取开奖号码（在标题下方的表格中）
    # 先找到包含标题的表格
    table = toto_header.find_parent("table")
    if not table:
        print("⚠️ 警告：未找到包含标题的表格，尝试其他方式...")
        # 备用方案：查找所有表格，寻找包含数字的
        all_tables = soup.find_all("table")
        for t in all_tables:
            if "6" in t.get_text() and "8" in t.get_text() and "28" in t.get_text():  # 简单的特征匹配
                table = t
                print("✅ 通过特征找到号码表格")
                break
        if not table:
            print("❌ 无法找到号码表格")
            return data

    # 在表格中寻找号码行（通常包含多个数字和 "+"）
    rows = table.find_all("tr")
    found_numbers = False
    for row in rows:
        cells = row.find_all("td")
        row_text = row.get_text()
        # 如果这一行包含数字且数量合理，可能是号码行
        if len(cells) >= 5 and "+" in row_text:
            for cell in cells:
                text = cell.get_text(strip=True)
                if text and text.isdigit():
                    data["winning_numbers"].append(text)
                elif text == "+":
                    # 忽略加号
                    pass
            if data["winning_numbers"]:
                found_numbers = True
                print(f"✅ 提取到开奖号码: {' '.join(data['winning_numbers'])}")
                break

    if not found_numbers:
        print("⚠️ 未在表格中找到开奖号码")

    # 4. 提取奖金分配表
    # 查找包含 "Prize Group" 的单元格
    prize_header = soup.find("td", string=re.compile(r"Prize Group", re.I))
    if not prize_header:
        print("⚠️ 未找到 'Prize Group' 标题，跳过奖金表")
        return data

    prize_table = prize_header.find_parent("table")
    if prize_table:
        prize_rows = prize_table.find_all("tr")
        # 跳过表头行（第一行）
        for row in prize_rows[1:]:
            cells = row.find_all("td")
            if len(cells) >= 3:
                group = cells[0].get_text(strip=True)
                amount = cells[1].get_text(strip=True)
                winners = cells[2].get_text(strip=True)
                # 处理可能为空的 Group 1
                if not amount and not winners:
                    amount = ""
                    winners = ""
                data["prize_table"].append([group, amount, winners])
        print(f"✅ 提取到 {len(data['prize_table'])} 行奖金数据")
    else:
        print("⚠️ 未找到奖金分配表格")

    return data

# ---------- 保存 JSON 和索引更新 ----------
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

# ---------- 主流程 ----------
def main():
    # 1. 抓取 4d4d.co 数据
    html_4d4d = fetch_html(URL_4D4D)
    if html_4d4d:
        soup_4d4d = BeautifulSoup(html_4d4d, "html.parser")
        global_date, global_draw_no = extract_global_date(soup_4d4d)
        print(f"🌍 4d4d.co 全局日期: {global_date}, 全局期号: {global_draw_no}")
        outer_boxes = soup_4d4d.find_all("div", class_="outerbox")
        print(f"📦 找到 {len(outer_boxes)} 个 outerbox")

        company_matchers = [
            (re.compile(r'GRAND\s+DRAGON', re.I), 'grand_dragon', extract_grand_dragon),
            (re.compile(r'DAMACAI.*4D', re.I), 'damacai', extract_damacai),
            (re.compile(r'MAGNUM.*4D', re.I), 'magnum', extract_magnum),
            (re.compile(r'TOTO.*4D', re.I), 'toto', extract_toto),
            (re.compile(r'SINGAPORE.*4D', re.I), 'singapore', extract_singapore),
            (re.compile(r'DA MA CAI 1\+3D', re.I), 'damacai_1p3d', extract_damacai_1p3d),
            (re.compile(r'SABAH.*88.*4D', re.I), 'sabah', extract_sabah),
            (re.compile(r'SANDAKAN.*4D', re.I), 'sandakan', extract_sandakan),
            (re.compile(r'CASHWEEP.*4D', re.I), 'sarawak_cashsweep', extract_cashsweep),
            (re.compile(r'SPORTSTOTO.*5D', re.I), 'sportstoto_5d', extract_sportstoto_5d),
            (re.compile(r'SPORTSTOTO.*6D', re.I), 'sportstoto_6d', extract_sportstoto_6d),
            (re.compile(r'SPORTSTOTO.*LOTTO', re.I), 'sportstoto_lotto', extract_sportstoto_lotto),
        ]

        processed_companies = set()
        for idx, box in enumerate(outer_boxes):
            box_text = box.get_text(" ", strip=True)
            matched = False
            for pattern, company_key, extract_func in company_matchers:
                if pattern.search(box_text):
                    print(f"🔍 处理 {company_key} (outerbox {idx})")
                    data = extract_func(box, global_date, global_draw_no)
                    if 'data' in data and isinstance(data['data'], list):
                        print(f"  提取到 {len(data['data'])} 条 {company_key} 数据")
                    save_json(company_key, data)
                    processed_companies.add(company_key)
                    matched = True
            if not matched:
                if "SPORTSTOTO" in box_text.upper():
                    print(f"🔍 尝试提取 SportsToto 复合数据 (outerbox {idx})")
                    data_5d = extract_sportstoto_5d(box, global_date, global_draw_no)
                    if data_5d.get('data'):
                        print(f"  提取到 {len(data_5d['data'])} 条 5D 数据")
                        save_json('sportstoto_5d', data_5d)
                        processed_companies.add('sportstoto_5d')
                    data_6d = extract_sportstoto_6d(box, global_date, global_draw_no)
                    if data_6d.get('data'):
                        print(f"  提取到 {len(data_6d['data'])} 条 6D 数据")
                        save_json('sportstoto_6d', data_6d)
                        processed_companies.add('sportstoto_6d')
                    data_lotto = extract_sportstoto_lotto(box, global_date, global_draw_no)
                    if data_lotto.get('star') or data_lotto.get('power') or data_lotto.get('supreme'):
                        save_json('sportstoto_lotto', data_lotto)
                        processed_companies.add('sportstoto_lotto')
                else:
                    print(f"⚠️ 未识别的 outerbox {idx}，内容: {box_text[:100]}...")

        all_possible = {key for _, key, _ in company_matchers}
        all_possible.update(['sportstoto_5d', 'sportstoto_6d', 'sportstoto_lotto'])
        missing = all_possible - processed_companies
        if missing:
            print(f"ℹ️ 以下公司当天无数据: {', '.join(missing)}")

    # 2. 从 4dmoon.com 抓取 Singapore Toto
    print("\n🌙 正在从 4dmoon.com 抓取 Singapore Toto...")
    html_moon = fetch_html("https://www.4dmoon.com/singapore-4d-results/")
    if html_moon:
        soup_moon = BeautifulSoup(html_moon, "html.parser")
        toto_data = extract_singapore_toto_4dmoon(soup_moon)
        if toto_data:
            save_json('singapore_toto', toto_data)
        else:
            print("⚠️ Singapore Toto 无有效数据")
    else:
        print("❌ 无法获取 4dmoon.com 页面")

    update_dates_index()

if __name__ == "__main__":
    main()
