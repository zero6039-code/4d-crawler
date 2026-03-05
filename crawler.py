import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import re

# ---------- 配置 ----------
URL = "https://4d4d.co/"
URL_4DMOON = "https://www.4dmoon.com"

# ---------- 原 4d4d.co 提取函数（保持不变） ----------
def extract_damacai(box, global_date, global_draw_no):
    return base_extract(box, global_date, global_draw_no)

def extract_magnum(box, global_date, global_draw_no):
    return base_extract(box, global_date, global_draw_no)

def extract_toto(box, global_date, global_draw_no):
    return base_extract(box, global_date, global_draw_no)

def extract_singapore(box, global_date, global_draw_no):
    """Singapore 4D 专用提取（不依赖 resultbottom 类）"""
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

# ---------- 通用基础提取 ----------
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

# ---------- 特殊表格提取 ----------
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
    h5 = box.find("td", string=re.compile("5D"))
    if not h5:
        return []
    table = h5.find_parent("table")
    if not table:
        return []
    rows = table.find_all("tr")
    data = []
    for row in rows[1:]:
        tds = row.find_all("td")
        if len(tds) >= 2:
            data.append([tds[0].get_text(strip=True), tds[1].get_text(strip=True)])
    return data

def extract_6d_table(box):
    h6 = box.find("td", string=re.compile("6D"))
    if not h6:
        return []
    table = h6.find_parent("table")
    if not table:
        return []
    rows = table.find_all("tr")
    data = []
    for row in rows[1:]:
        tds = row.find_all("td")
        if len(tds) >= 4:
            data.append([
                tds[0].get_text(strip=True),
                tds[1].get_text(strip=True),
                tds[3].get_text(strip=True) if len(tds) > 3 else ''
            ])
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
    supreme_section = box.find("td", string=re.compile("Supreme Toto 6/58"))
    if supreme_section:
        table = supreme_section.find_parent("table")
        if table:
            rows = table.find_all("tr")
            if len(rows) >= 2:
                num_row = rows[1]
                tds = num_row.find_all("td", class_="resultbottomtoto2")
                supreme = [td.get_text(strip=True) for td in tds]
    return star, power, supreme, jackpots

# ---------- 4dmoon.com 抓取函数（新增）----------
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

def parse_4dmoon_date(date_str):
    """将 04-Mar-2026 转换为 04-03-2026"""
    try:
        d = datetime.strptime(date_str.strip(), "%d-%b-%Y")
        return d.strftime("%d-%m-%Y")
    except:
        return None

def extract_grand_dragon_4dmoon(soup):
    """从 4dmoon.com 提取 Grand Dragon 4D 数据"""
    data = {"draw_date": "", "draw_no": "", "1st": "", "2nd": "", "3rd": "", "special": [], "consolation": []}
    section = soup.find("td", string=re.compile(r"Grand Dragon 4D", re.I))
    if not section:
        return None
    parent = section.find_parent("td")
    if parent:
        text = parent.get_text(" ", strip=True)
        date_match = re.search(r"(\d{2}-[A-Za-z]{3}-\d{4})", text)
        if date_match:
            data["draw_date"] = parse_4dmoon_date(date_match.group(1))
    table = section.find_parent("table")
    if table:
        rows = table.find_all("tr")
        # 尝试提取前三名（假设它们位于某些特定位置，需要根据实际页面调整）
        # 这里仅作示例，您可能需要根据页面源码精确选择
        prize_cells = table.find_all("td", class_=re.compile(r"prize|resulttop", re.I))
        if len(prize_cells) >= 3:
            data["1st"] = prize_cells[0].get_text(strip=True)
            data["2nd"] = prize_cells[1].get_text(strip=True)
            data["3rd"] = prize_cells[2].get_text(strip=True)
        # 特别奖和安慰奖提取类似，需要具体实现
    return data

def extract_sportstoto_fireball_4dmoon(soup):
    """提取 SportsToto Fireball 数据"""
    data = {"draw_date": "", "draw_no": "", "data": []}
    section = soup.find("td", string=re.compile(r"SportsToto Fireball", re.I))
    if not section:
        return None
    parent = section.find_parent("td")
    if parent:
        text = parent.get_text(" ", strip=True)
        date_match = re.search(r"(\d{2}-[A-Za-z]{3}-\d{4})", text)
        if date_match:
            data["draw_date"] = parse_4dmoon_date(date_match.group(1))
        no_match = re.search(r"#(\d+/\d+)", text)
        if no_match:
            data["draw_no"] = no_match.group(1)
    table = section.find_parent("table")
    if table:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 2:
                data["data"].append([cells[0].get_text(strip=True), cells[1].get_text(strip=True)])
    return data

def extract_sportstoto_5d_4dmoon(soup):
    """提取 SportsToto 5D 数据"""
    data = {"draw_date": "", "draw_no": "", "data": []}
    section = soup.find("td", string=re.compile(r"SportsToto 5D", re.I))
    if not section:
        return None
    parent = section.find_parent("td")
    if parent:
        text = parent.get_text(" ", strip=True)
        date_match = re.search(r"(\d{2}-[A-Za-z]{3}-\d{4})", text)
        if date_match:
            data["draw_date"] = parse_4dmoon_date(date_match.group(1))
        no_match = re.search(r"#(\d+/\d+)", text)
        if no_match:
            data["draw_no"] = no_match.group(1)
    table = section.find_parent("table")
    if table:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 2:
                data["data"].append([cells[0].get_text(strip=True), cells[1].get_text(strip=True)])
    return data

def extract_sportstoto_6d_4dmoon(soup):
    """提取 SportsToto 6D 数据（包含 or 备选号码）"""
    data = {"draw_date": "", "draw_no": "", "data": []}
    section = soup.find("td", string=re.compile(r"SportsToto 6D", re.I))
    if not section:
        return None
    parent = section.find_parent("td")
    if parent:
        text = parent.get_text(" ", strip=True)
        date_match = re.search(r"(\d{2}-[A-Za-z]{3}-\d{4})", text)
        if date_match:
            data["draw_date"] = parse_4dmoon_date(date_match.group(1))
        no_match = re.search(r"#(\d+/\d+)", text)
        if no_match:
            data["draw_no"] = no_match.group(1)
    table = section.find_parent("table")
    if table:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 3:
                # 假设格式：排名 | 主号码 | "or" | 备选号码
                data["data"].append([
                    cells[0].get_text(strip=True),
                    cells[1].get_text(strip=True),
                    cells[3].get_text(strip=True) if len(cells) > 3 else ''
                ])
    return data

def extract_sportstoto_lotto_4dmoon(soup):
    """提取 SportsToto Lotto (Star/Power/Supreme) 数据"""
    data = {"draw_date": "", "draw_no": "", "star": [], "power": [], "supreme": [], "jackpots": []}
    # 提取 Star Toto
    star_section = soup.find("td", string=re.compile(r"Star Toto 6/50", re.I))
    if star_section:
        table = star_section.find_parent("table")
        if table:
            rows = table.find_all("tr")
            if len(rows) >= 2:
                num_row = rows[1]
                tds = num_row.find_all("td")
                data["star"] = [td.get_text(strip=True) for td in tds if td.get_text(strip=True) not in ['+', '']]
            for row in rows[2:]:
                jp_tds = row.find_all("td")
                if jp_tds:
                    data["jackpots"].append(jp_tds[0].get_text(strip=True))
    # 提取 Power Toto
    power_section = soup.find("td", string=re.compile(r"Power Toto 6/55", re.I))
    if power_section:
        table = power_section.find_parent("table")
        if table:
            rows = table.find_all("tr")
            if len(rows) >= 2:
                num_row = rows[1]
                tds = num_row.find_all("td")
                data["power"] = [td.get_text(strip=True) for td in tds]
    # 提取 Supreme Toto
    supreme_section = soup.find("td", string=re.compile(r"Supreme Toto 6/58", re.I))
    if supreme_section:
        table = supreme_section.find_parent("table")
        if table:
            rows = table.find_all("tr")
            if len(rows) >= 2:
                num_row = rows[1]
                tds = num_row.find_all("td")
                data["supreme"] = [td.get_text(strip=True) for td in tds]
    return data

def extract_magnum_jackpot_gold_4dmoon(soup):
    """提取 Magnum 4D Jackpot Gold 数据"""
    data = {"draw_date": "", "draw_no": "", "data": []}
    section = soup.find("td", string=re.compile(r"4D Jackpot Estimated Amount", re.I))
    if not section:
        return None
    parent = section.find_parent("td")
    if parent:
        text = parent.get_text(" ", strip=True)
        date_match = re.search(r"(\d{2}-[A-Za-z]{3}-\d{4})", text)
        if date_match:
            data["draw_date"] = parse_4dmoon_date(date_match.group(1))
        no_match = re.search(r"#(\d+/\d+)", text)
        if no_match:
            data["draw_no"] = no_match.group(1)
    table = section.find_parent("table")
    if table:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 2:
                data["data"].append([cells[0].get_text(strip=True), cells[1].get_text(strip=True)])
    return data

def extract_singapore_toto_4dmoon(soup):
    """提取 Singapore Toto 数据"""
    data = {"draw_date": "", "draw_no": "", "winning_numbers": [], "prize_table": []}
    section = soup.find("td", string=re.compile(r"Singapore Toto", re.I))
    if not section:
        return None
    parent = section.find_parent("td")
    if parent:
        text = parent.get_text(" ", strip=True)
        date_match = re.search(r"(\d{2}-[A-Za-z]{3}-\d{4})", text)
        if date_match:
            data["draw_date"] = parse_4dmoon_date(date_match.group(1))
        no_match = re.search(r"#(\d+)", text)
        if no_match:
            data["draw_no"] = no_match.group(1)
    table = section.find_parent("table")
    if table:
        rows = table.find_all("tr")
        if len(rows) >= 2:
            num_row = rows[1]
            tds = num_row.find_all("td")
            data["winning_numbers"] = [td.get_text(strip=True) for td in tds if td.get_text(strip=True) and td.get_text(strip=True) != '+']
        # 奖组表格可能在下一个 table 中
        prize_table = table.find_next("table")
        if prize_table:
            prize_rows = prize_table.find_all("tr")
            for row in prize_rows[1:]:
                cells = row.find_all("td")
                if len(cells) >= 3:
                    data["prize_table"].append([cells[0].get_text(strip=True), cells[1].get_text(strip=True), cells[2].get_text(strip=True)])
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

# ---------- 原 4d4d.co 主流程（保持不变）----------
def main_4d4d():
    html = fetch_html()
    if not html:
        return None, None
    soup = BeautifulSoup(html, "html.parser")
    global_date, global_draw_no = extract_global_date(soup)
    print(f"🌍 全局日期: {global_date}, 全局期号: {global_draw_no}")
    outer_boxes = soup.find_all("div", class_="outerbox")
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
                save_json(company_key, data)
                processed_companies.add(company_key)
                matched = True
        if not matched:
            if "SPORTSTOTO" in box_text.upper():
                print(f"🔍 尝试提取 SportsToto 复合数据 (outerbox {idx})")
                data_5d = extract_sportstoto_5d(box, global_date, global_draw_no)
                if data_5d.get('data'):
                    save_json('sportstoto_5d', data_5d)
                    processed_companies.add('sportstoto_5d')
                data_6d = extract_sportstoto_6d(box, global_date, global_draw_no)
                if data_6d.get('data'):
                    save_json('sportstoto_6d', data_6d)
                    processed_companies.add('sportstoto_6d')
                data_lotto = extract_sportstoto_lotto(box, global_date, global_draw_no)
                if data_lotto.get('star') or data_lotto.get('power') or data_lotto.get('supreme'):
                    save_json('sportstoto_lotto', data_lotto)
                    processed_companies.add('sportstoto_lotto')
            else:
                print(f"⚠️ 未识别的 outerbox {idx}，内容: {box_text[:100]}...")
    return processed_companies, global_date

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

        # 定义需要从 4dmoon 抓取的公司及其提取函数
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
                    # 如果公司已经在 4d4d 中处理过且数据非空，可以选择覆盖或保留，这里直接保存
                    save_json(company_key, data)
                else:
                    print(f"⚠️ {company_key} 无有效数据")
            except Exception as e:
                print(f"❌ 处理 {company_key} 时出错: {e}")

    update_dates_index()

if __name__ == "__main__":
    main()
