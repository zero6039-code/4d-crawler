import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import re
import time
import sqlite3
from urllib.parse import urljoin

# ---------- 配置 ----------
URL_4D4D = "https://4d4d.co/"
URL_4DLATEST = "https://4dlatest.org/"
URL_4D2ULIVE = "https://4d2ulive.com"
DB_PATH = '4d_results.db'  # SQLite 数据库文件

# ---------- 数据库辅助函数 ----------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

def insert_number(company, type_, number, draw_date):
    """
    将单个号码插入数据库，如果已存在则跳过
    company: 公司键（如 'damacai'）
    type_: 号码类型（如 'special', 'consolation', '1st' 等）
    number: 号码字符串
    draw_date: 开奖日期，格式 'dd-mm-yyyy'
    """
    if not number or number == '----':
        return
    conn = get_db_connection()
    c = conn.cursor()
    # 检查是否已存在
    c.execute('''
        SELECT id FROM results 
        WHERE company = ? AND type = ? AND number = ? AND draw_date = ?
    ''', (company, type_, number, draw_date))
    if c.fetchone() is None:
        c.execute('''
            INSERT INTO results (company, type, number, draw_date)
            VALUES (?, ?, ?, ?)
        ''', (company, type_, number, draw_date))
        conn.commit()
        print(f"   💾 插入数据库: {company} {type_} {number} {draw_date}")
    else:
        print(f"   🔁 已存在: {company} {type_} {number}")
    conn.close()

def store_numbers_from_data(company, data):
    """
    从数据对象中提取所有号码并存入数据库
    """
    draw_date = data.get('draw_date')
    if not draw_date or draw_date == '----':
        draw_date = datetime.now().strftime("%d-%m-%Y")

    # 常见号码字段
    prize_fields = ['1st', '2nd', '3rd']
    list_fields = ['special', 'consolation', 'winning_numbers', 'star', 'power', 'supreme']
    
    # 处理单个奖项
    for field in prize_fields:
        num = data.get(field)
        if num and num != '----':
            insert_number(company, field, num, draw_date)
    
    # 处理列表奖项
    for field in list_fields:
        nums = data.get(field, [])
        if isinstance(nums, list):
            for num in nums:
                if num and num != '----':
                    insert_number(company, field, num, draw_date)
    
    # 特殊处理：sportstoto_6d 的嵌套结构
    if company == 'sportstoto_6d':
        for pos in ['2nd', '3rd', '4th', '5th']:
            item = data.get(pos, {})
            if isinstance(item, dict):
                main = item.get('main')
                alt = item.get('alt')
                if main:
                    insert_number(company, f'{pos}_main', main, draw_date)
                if alt:
                    insert_number(company, f'{pos}_alt', alt, draw_date)
    
    # 特殊处理：magnum_jackpot_gold 的 groups（可选）
    if company == 'magnum_jackpot_gold':
        groups = data.get('groups', [])
        for grp in groups:
            grp_num = grp.get('group')
            nums = grp.get('numbers', [])
            # 将组内号码插入，类型为 'group_X'
            for num in nums:
                if num and num != '+':
                    insert_number(company, f'group_{grp_num}', num, draw_date)

# ---------- 辅助函数 ----------
def fetch_html(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        print(f"🌐 正在请求: {url}")
        r = requests.get(url, headers=headers, timeout=15)
        print(f"  状态码: {r.status_code}")
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

# ---------- 4d4d.co 基础提取 ----------
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

def extract_grand_dragon(box, global_date, global_draw_no):
    return base_extract(box, global_date, global_draw_no)

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

# ---------- Sports Toto 5D 提取 ----------
def extract_sportstoto_5d(box, global_date, global_draw_no):
    data = {
        "draw_date": global_date,
        "draw_no": global_draw_no,
        "type": "5d",
        "1st": "",
        "2nd": "",
        "3rd": "",
        "4th": "",
        "5th": "",
        "6th": ""
    }
    header = box.find("td", string=re.compile(r"5D", re.IGNORECASE))
    if not header:
        return data
    table = header.find_parent("table")
    if not table:
        return data
    rows = table.find_all("tr")
    for row in rows:
        tds = row.find_all("td")
        if len(tds) < 2:
            continue
        label = tds[0].get_text(strip=True).lower()
        number = tds[1].get_text(strip=True) if len(tds) > 1 else ""
        if "1st" in label:
            data["1st"] = number
        elif "2nd" in label:
            data["2nd"] = number
        elif "3rd" in label:
            data["3rd"] = number
        elif "4th" in label:
            data["4th"] = number
        elif "5th" in label:
            data["5th"] = number
        elif "6th" in label:
            data["6th"] = number
    return data

# ---------- Sports Toto 6D 提取 ----------
def extract_6d_pair(row_text):
    row_text = re.sub(r'^(2nd|3rd|4th|5th)', '', row_text, flags=re.IGNORECASE).strip()
    parts = re.split(r'\s+or\s+', row_text, flags=re.IGNORECASE)
    if len(parts) >= 2:
        main = parts[0].strip()
        alt = parts[1].strip()
    else:
        main = row_text
        alt = ""
    return main, alt

def extract_sportstoto_6d(box, global_date, global_draw_no):
    data = {
        "draw_date": global_date,
        "draw_no": global_draw_no,
        "type": "6d",
        "1st": "",
        "2nd": {"main": "", "alt": ""},
        "3rd": {"main": "", "alt": ""},
        "4th": {"main": "", "alt": ""},
        "5th": {"main": "", "alt": ""}
    }
    header = box.find("td", string=re.compile(r"6D", re.IGNORECASE))
    if not header:
        return data
    table = header.find_parent("table")
    if not table:
        return data
    rows = table.find_all("tr")
    for row in rows:
        row_text = row.get_text()
        tds = row.find_all("td")
        if len(tds) < 2:
            continue
        label = tds[0].get_text(strip=True).lower()
        if "1st" in label:
            if len(tds) >= 2:
                data["1st"] = tds[1].get_text(strip=True)
        elif "2nd" in label:
            main, alt = extract_6d_pair(row_text)
            data["2nd"]["main"] = main
            data["2nd"]["alt"] = alt
        elif "3rd" in label:
            main, alt = extract_6d_pair(row_text)
            data["3rd"]["main"] = main
            data["3rd"]["alt"] = alt
        elif "4th" in label:
            main, alt = extract_6d_pair(row_text)
            data["4th"]["main"] = main
            data["4th"]["alt"] = alt
        elif "5th" in label:
            main, alt = extract_6d_pair(row_text)
            data["5th"]["main"] = main
            data["5th"]["alt"] = alt
    return data

# ---------- Sports Toto Lotto 提取 ----------
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
    while len(jackpots) < 4:
        jackpots.append("")
    return star, power, supreme, jackpots

def extract_sportstoto_lotto(box, global_date, global_draw_no):
    data = base_extract(box, global_date, global_draw_no)
    data['type'] = 'lotto'
    data['star'], data['power'], data['supreme'], data['jackpots'] = extract_lotto(box)
    return data

# ================== 优化后的核心提取函数 ==================

# ---------- 从 4dlatest.org 精确提取 GDLOTTO 豪龙数据 (最终修复版) ----------
def extract_gd_lotto_from_4dlatest(soup):
    print("🔍 正在从 4dlatest.org 精确提取 GDLOTTO 豪龙数据...")
    data = {
        "draw_date": "",
        "draw_no": "",
        "1st": "",
        "2nd": "",
        "3rd": "",
        "special": [],
        "consolation": [],
        "jackpot": ""
    }

    # 1. 精确查找包含 "GDLOTTO 豪龙" 的标题元素
    header_element = soup.find(string=re.compile(r'GDLOTTO\s*豪龙', re.I))
    if not header_element:
        print("⚠️ 未找到标题为 'GDLOTTO 豪龙' 的元素")
        return None

    # 获取标题所在的单元格，提取完整文本（可能包含日期）
    parent_cell = header_element.find_parent('td')
    if parent_cell:
        header_text = parent_cell.get_text(" ", strip=True)
    else:
        header_text = header_element.get_text(" ", strip=True)

    print(f"📅 标题文本: {header_text}")

    # 2. 获取该标题所在的表格
    target_table = header_element.find_parent('table')
    if not target_table:
        target_table = header_element.find_next('table')
    if not target_table:
        print("⚠️ 未找到 GDLOTTO 豪龙的数据表格")
        return None

    # 3. 从标题文本中提取日期和期号
    # 支持多种格式：dd/mm/yyyy, dd-mm-yyyy, dd mmm yyyy
    date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})', header_text)
    if not date_match:
        date_match = re.search(r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})', header_text)
    if date_match:
        raw_date = date_match.group(1)
        try:
            if re.match(r'\d{1,2}\s+[A-Za-z]{3}\s+\d{4}', raw_date):
                d = datetime.strptime(raw_date, "%d %b %Y")
                data["draw_date"] = d.strftime("%d-%m-%Y")
            else:
                sep = '/' if '/' in raw_date else '-'
                d = datetime.strptime(raw_date, f"%d{sep}%m{sep}%Y")
                data["draw_date"] = d.strftime("%d-%m-%Y")
            print(f"  ✅ 提取到日期: {data['draw_date']}")
        except Exception as e:
            print(f"  ⚠️ 日期解析失败: {e}")
    else:
        print("  ⚠️ 未找到日期信息")

    # 期号匹配
    no_match = re.search(r'#?(\d+/\d+)', header_text)
    if no_match:
        data["draw_no"] = no_match.group(1)
        print(f"  ✅ 提取到期号: {data['draw_no']}")
    else:
        # 如果标题行没有期号，尝试从表格第一行查找
        first_row = target_table.find('tr')
        if first_row:
            row_text = first_row.get_text()
            no_match = re.search(r'#?(\d+/\d+)', row_text)
            if no_match:
                data["draw_no"] = no_match.group(1)
                print(f"  ✅ 从第一行提取到期号: {data['draw_no']}")

    # 4. 遍历表格行提取号码
    rows = target_table.find_all("tr")
    special_mode = False
    consolation_mode = False
    special_list = []
    consolation_list = []

    for row in rows:
        row_text = row.get_text().upper()
        cells = row.find_all("td")

        # 切换模式
        if "SPECIAL" in row_text:
            special_mode = True
            consolation_mode = False
            for cell in cells:
                num = cell.get_text(strip=True)
                if num.isdigit() and len(num) == 4:
                    special_list.append(num)
            continue
        if "CONSOLATION" in row_text:
            special_mode = False
            consolation_mode = True
            for cell in cells:
                num = cell.get_text(strip=True)
                if num.isdigit() and len(num) == 4:
                    consolation_list.append(num)
            continue
        if "JACKPOT" in row_text or "USD" in row_text:
            amount_match = re.search(r'([\d,]+(?:\.\d+)?)', row.get_text())
            if amount_match:
                data["jackpot"] = amount_match.group(1)
            continue

        # 提取前三
        if "1ST" in row_text:
            for cell in cells:
                num = cell.get_text(strip=True)
                if num.isdigit() and len(num) == 4:
                    data["1st"] = num
                    break
        if "2ND" in row_text:
            for cell in cells:
                num = cell.get_text(strip=True)
                if num.isdigit() and len(num) == 4:
                    data["2nd"] = num
                    break
        if "3RD" in row_text:
            for cell in cells:
                num = cell.get_text(strip=True)
                if num.isdigit() and len(num) == 4:
                    data["3rd"] = num
                    break

        # 如果在模式中，继续收集
        if special_mode:
            for cell in cells:
                num = cell.get_text(strip=True)
                if num.isdigit() and len(num) == 4:
                    special_list.append(num)
        if consolation_mode:
            for cell in cells:
                num = cell.get_text(strip=True)
                if num.isdigit() and len(num) == 4:
                    consolation_list.append(num)

    data["special"] = list(dict.fromkeys(special_list))[:10]
    data["consolation"] = list(dict.fromkeys(consolation_list))[:10]

    print(f"  提取到前三: {data['1st']}, {data['2nd']}, {data['3rd']}")
    print(f"  特别奖数量: {len(data['special'])}")
    print(f"  安慰奖数量: {len(data['consolation'])}")
    print(f"  Jackpot: {data['jackpot']}")
    return data

# ---------- 从 4dmoon.com 获取新加坡 4D & TOTO 数据 (区域定位最终版) ----------
def fetch_singapore_from_4dmoon():
    print("🔍 正在从 4dmoon.com 获取新加坡 4D & TOTO 数据...")
    url = "https://www.4dmoon.com/singapore-4d-results/"
    html = fetch_html(url)
    if not html:
        return None, None

    soup = BeautifulSoup(html, "html.parser")
    # 获取纯文本并保留换行
    text = soup.get_text()
    lines = text.splitlines()

    singapore_4d_data = {"draw_date": "", "draw_no": "", "1st": "", "2nd": "", "3rd": "", "special": [], "consolation": []}
    singapore_toto_data = {"draw_date": "", "draw_no": "", "winning_numbers": [], "prize_table": []}

    # ---------- 新加坡 4D 部分（保持原有简单提取）----------
    if 'Singapore 4D' in text:
        date_match = re.search(r'Singapore\s*4D.*?\([A-Za-z]{3}\)\s*(\d{1,2}-[A-Za-z]{3}-\d{4})', text, re.DOTALL)
        if date_match:
            try:
                d = datetime.strptime(date_match.group(1), "%d-%b-%Y")
                singapore_4d_data["draw_date"] = d.strftime("%d-%m-%Y")
                print(f"    ✅ 4D 日期: {singapore_4d_data['draw_date']}")
            except:
                pass
        no_match = re.search(r'#(\d+)', text)
        if no_match:
            singapore_4d_data["draw_no"] = no_match.group(1)
            print(f"    ✅ 4D 期号: {singapore_4d_data['draw_no']}")

    # ---------- 新加坡 TOTO 部分（区域定位法）----------
    # 1. 定位 "Singapore Toto" 区域
    toto_start = None
    for i, line in enumerate(lines):
        if 'Singapore Toto' in line:
            toto_start = i
            break

    if toto_start is not None:
        print("  ✅ 找到新加坡 TOTO 数据")
        # 提取日期（从标题行）
        header_line = lines[toto_start]
        date_match = re.search(r'\([A-Za-z]{3}\)\s*(\d{1,2}-[A-Za-z]{3}-\d{4})', header_line)
        if date_match:
            try:
                d = datetime.strptime(date_match.group(1), "%d-%b-%Y")
                singapore_toto_data["draw_date"] = d.strftime("%d-%m-%Y")
                print(f"    ✅ TOTO 日期: {singapore_toto_data['draw_date']}")
            except:
                pass

        # 2. 从标题行之后查找期号（通常在下一行或附近）
        for j in range(toto_start + 1, min(toto_start + 5, len(lines))):
            line = lines[j].strip()
            if line.startswith('#'):
                singapore_toto_data["draw_no"] = line[1:].strip()
                print(f"    ✅ TOTO 期号: {singapore_toto_data['draw_no']}")
                break

        # 3. 查找号码行（包含 "+" 的行）
        numbers_line = None
        for j in range(toto_start + 1, toto_start + 20):  # 向下搜索20行
            if j >= len(lines):
                break
            line = lines[j].strip()
            if '+' in line and re.search(r'\d+\s*\+\s*\d+', line):
                numbers_line = line
                break

        if numbers_line:
            # 提取所有数字
            all_nums = re.findall(r'\b(\d{1,2})\b', numbers_line)
            if all_nums:
                # 通常前6个是主号码，最后一个是额外号码
                if len(all_nums) >= 7:
                    singapore_toto_data["winning_numbers"] = all_nums[:6] + [all_nums[-1]]
                else:
                    singapore_toto_data["winning_numbers"] = all_nums
                print(f"    ✅ TOTO 号码: {' '.join(singapore_toto_data['winning_numbers'])}")

        # 4. 查找奖金表（从 "Prize Group" 开始）
        prize_start = None
        for j in range(toto_start + 1, len(lines)):
            if 'Prize Group' in lines[j]:
                prize_start = j
                break

        if prize_start:
            # 从下一行开始解析表格
            for j in range(prize_start + 1, len(lines)):
                line = lines[j].strip()
                if not line or (line.startswith('|') is False and '|' not in line):
                    # 空行或非表格行结束
                    break
                # 处理可能没有竖线开头的行
                parts = re.split(r'\s*\|\s*', line)
                if len(parts) >= 3:
                    group = parts[0].strip()
                    amount = parts[1].strip() if parts[1] else ""
                    winners = parts[2].strip() if len(parts) > 2 else ""
                    singapore_toto_data["prize_table"].append([group, amount, winners])

        print(f"    ✅ TOTO 奖金表行数: {len(singapore_toto_data['prize_table'])}")

    return singapore_4d_data, singapore_toto_data

# ---------- 从 4dlatest.org 提取 SABAH88 沙巴万字 LOTTO ----------
def extract_sabah_lotto_from_4dlatest(soup):
    print("🔍 正在从 4dlatest.org 提取 SABAH88 沙巴万字 LOTTO 数据...")
    data = {
        "draw_date": "",
        "draw_no": "",
        "winning_numbers": [],
        "jackpot1": "",
        "jackpot2": ""
    }

    # 1. 查找包含 "SABAH88" 和 "LOTTO" 的标题，用于定位表格
    header = soup.find(string=re.compile(r"SABAH88.*LOTTO", re.IGNORECASE))
    if not header:
        print("❌ 未找到 'SABAH88 LOTTO' 标题")
        return None

    table = header.find_parent("table")
    if not table:
        table = header.find_next("table")
    if not table:
        print("❌ 未找到数据表格")
        return None

    # 2. 提取开奖号码
    rows = table.find_all("tr")
    for row in rows:
        row_text = row.get_text()
        cells = row.find_all("td")
        if "+" in row_text:
            numbers = []
            for cell in cells:
                text = cell.get_text(strip=True)
                if text.isdigit():
                    numbers.append(text)
                elif text == "+":
                    pass
            if numbers:
                data["winning_numbers"] = numbers
                print(f"✅ 提取到开奖号码: {' '.join(numbers)}")
            break

    # 3. 提取日期和期号（在整个页面中搜索第一个有效日期）
    def find_date_and_no():
        date_patterns = [
            r'(\d{2}/\d{2}/\d{4})',   # dd/mm/yyyy
            r'(\d{2}-\d{2}-\d{4})'    # dd-mm-yyyy
        ]
        for text_node in soup.find_all(string=True):
            text = text_node.strip()
            for pat in date_patterns:
                date_match = re.search(pat, text)
                if date_match:
                    raw_date = date_match.group(1)
                    if '/' in raw_date:
                        parts = raw_date.split('/')
                    else:
                        parts = raw_date.split('-')
                    if len(parts) == 3:
                        formatted_date = f"{parts[0]}-{parts[1]}-{parts[2]}"
                    else:
                        formatted_date = raw_date.replace('/', '-')
                    # 尝试从同一文本中提取期号（如 4166/26）
                    no_match = re.search(r'(\d+/\d+)', text)
                    draw_no = no_match.group(1) if no_match else ""
                    return formatted_date, draw_no
        return "", ""

    date, draw_no = find_date_and_no()
    if date:
        data["draw_date"] = date
        print(f"  ✅ 提取到日期: {date}")
    if draw_no:
        data["draw_no"] = draw_no
        print(f"  ✅ 提取到期号: {draw_no}")

    # 4. 提取 Jackpot 金额（优先从包含 RM 的单元格）
    jackpots = []
    rm_cells = table.find_all(string=re.compile(r'RM'))
    for cell in rm_cells:
        parent_text = cell.parent.get_text() if cell.parent else cell
        amount_match = re.search(r'RM\s*([\d,]+(?:\.\d+)?)', parent_text)
        if amount_match:
            amount = amount_match.group(1)
            jackpots.append(amount)
    # 去重并按出现顺序保留前两个
    seen = set()
    unique_jackpots = []
    for jp in jackpots:
        if jp not in seen:
            seen.add(jp)
            unique_jackpots.append(jp)
    if len(unique_jackpots) >= 1:
        data["jackpot1"] = unique_jackpots[0]
        print(f"  ✅ Jackpot 1: {data['jackpot1']}")
    if len(unique_jackpots) >= 2:
        data["jackpot2"] = unique_jackpots[1]
        print(f"  ✅ Jackpot 2: {data['jackpot2']}")

    # 5. 如果 jackpot 金额还是 1 或 2（可能是占位符），使用备用方法提取大数字
    if data["jackpot1"] in ["1", "2"] or data["jackpot2"] in ["1", "2"]:
        print("  ⚠️ 检测到可能错误的 jackpot 金额，尝试备用提取方法...")
        all_numbers = []
        for row in rows:
            cells = row.find_all("td")
            for cell in cells:
                text = cell.get_text(strip=True)
                matches = re.findall(r'([\d,]+(?:\.\d+)?)', text)
                for m in matches:
                    try:
                        num = float(m.replace(',', ''))
                        if num > 1000:  # 假设金额大于1000
                            all_numbers.append(m)
                    except:
                        pass
        # 按数值大小降序排列
        all_numbers.sort(key=lambda x: float(x.replace(',', '')), reverse=True)
        if len(all_numbers) >= 1 and (data["jackpot1"] == "1" or data["jackpot1"] == ""):
            data["jackpot1"] = all_numbers[0]
            print(f"  ✅ 备用提取 Jackpot 1: {data['jackpot1']}")
        if len(all_numbers) >= 2 and (data["jackpot2"] == "2" or data["jackpot2"] == ""):
            data["jackpot2"] = all_numbers[1]
            print(f"  ✅ 备用提取 Jackpot 2: {data['jackpot2']}")

    return data

# ---------- 从 4dlatest.org 提取 Magnum Jackpot Gold ----------
def extract_magnum_jackpot_gold_from_4dlatest(soup):
    print("🔍 正在从 4dlatest.org 提取 MAGNUM JACKPOT GOLD 数据...")
    data = {
        "draw_date": "",
        "draw_no": "",
        "groups": [],
        "jackpots": []
    }
    header = soup.find(string=re.compile(r"MAGNUM.*JACKPOT.*GOLD", re.IGNORECASE))
    if not header:
        print("⚠️ 未找到 'MAGNUM JACKPOT GOLD' 标题")
        return None
    table = header.find_parent("table")
    if not table:
        table = header.find_next("table")
    if not table:
        print("⚠️ 未找到数据表格")
        return None
    header_text = header.get_text(" ", strip=True)
    print(f"📅 标题文本: {header_text}")
    date_match = re.search(r"(\d{2}/\d{2}/\d{4})", header_text)
    if date_match:
        try:
            d = datetime.strptime(date_match.group(1), "%d/%m/%Y")
            data["draw_date"] = d.strftime("%d-%m-%Y")
            print(f"  ✅ 提取到日期: {data['draw_date']}")
        except:
            pass
    no_match = re.search(r"(\d+/\d+)", header_text)
    if no_match:
        data["draw_no"] = no_match.group(1)
        print(f"  ✅ 提取到期号: {data['draw_no']}")

    rows = table.find_all("tr")
    current_group = None
    group_numbers = []
    for row in rows:
        row_text = row.get_text()
        cells = row.find_all("td")
        group_match = re.search(r"GROUP\s+(\d+)", row_text, re.I)
        if group_match:
            if current_group and group_numbers:
                data["groups"].append({"group": current_group, "numbers": group_numbers.copy()})
            current_group = group_match.group(1)
            group_numbers = []
            for cell in cells:
                text = cell.get_text(strip=True)
                if text.isdigit():
                    group_numbers.append(text)
                elif text == "+":
                    group_numbers.append("+")
            continue
        if current_group:
            for cell in cells:
                text = cell.get_text(strip=True)
                if text.isdigit():
                    group_numbers.append(text)
                elif text == "+":
                    group_numbers.append("+")
        if "Jackpot" in row_text or "RM" in row_text:
            amounts = re.findall(r'RM\s([\d,]+(?:.\d+)?)', row_text)
            if amounts:
                data["jackpots"].extend(amounts)
    if current_group and group_numbers:
        data["groups"].append({"group": current_group, "numbers": group_numbers.copy()})

    print(f"  提取到 {len(data['groups'])} 组号码")
    print(f"  提取到 {len(data['jackpots'])} 个奖池")
    return data

# ---------- 从 4dlatest.org 提取 Magnum Life ----------
def extract_magnum_life_from_4dlatest(soup):
    print("🔍 正在从 4dlatest.org 提取 MAGNUM LIFE 数据...")
    data = {
        "draw_date": "",
        "draw_no": "",
        "winning_numbers": [],
        "bonus_numbers": []
    }
    header = soup.find(string=re.compile(r"MAGNUM.*LIFE", re.IGNORECASE))
    if not header:
        print("⚠️ 未找到 'MAGNUM LIFE' 标题")
        return None
    table = header.find_parent("table")
    if not table:
        table = header.find_next("table")
    if not table:
        print("⚠️ 未找到数据表格")
        return None
    header_text = header.get_text(" ", strip=True)
    print(f"📅 标题文本: {header_text}")
    date_match = re.search(r"(\d{2}/\d{2}/\d{4})", header_text)
    if date_match:
        try:
            d = datetime.strptime(date_match.group(1), "%d/%m/%Y")
            data["draw_date"] = d.strftime("%d-%m-%Y")
            print(f"  ✅ 提取到日期: {data['draw_date']}")
        except:
            pass
    no_match = re.search(r"(\d+/\d+)", header_text)
    if no_match:
        data["draw_no"] = no_match.group(1)
        print(f"  ✅ 提取到期号: {data['draw_no']}")

    rows = table.find_all("tr")
    winning_mode = False
    bonus_mode = False
    for row in rows:
        row_text = row.get_text()
        cells = row.find_all("td")
        if "WINNING NUMBERS" in row_text.upper():
            winning_mode = True
            bonus_mode = False
            for cell in cells:
                text = cell.get_text(strip=True)
                if text.isdigit():
                    data["winning_numbers"].append(text)
            continue
        if "BONUS NUMBERS" in row_text.upper():
            winning_mode = False
            bonus_mode = True
            for cell in cells:
                text = cell.get_text(strip=True)
                if text.isdigit():
                    data["bonus_numbers"].append(text)
            continue
        if winning_mode:
            for cell in cells:
                text = cell.get_text(strip=True)
                if text.isdigit():
                    data["winning_numbers"].append(text)
        if bonus_mode:
            for cell in cells:
                text = cell.get_text(strip=True)
                if text.isdigit():
                    data["bonus_numbers"].append(text)
    print(f"  ✅ 提取到开奖号码: {' '.join(data['winning_numbers'])}")
    print(f"  ✅ 提取到特别号码: {' '.join(data['bonus_numbers'])}")
    return data

# ---------- 从 4dlatest.org 提取 Sports Toto 5D/6D/Lotto ----------
def extract_sportstoto_from_4dlatest(soup):
    print("🔍 正在从 4dlatest.org 提取 Sports Toto 5D/6D/Lotto 数据...")
    data_5d = {"draw_date": "", "draw_no": "", "type": "5d", "1st": "", "2nd": "", "3rd": "", "4th": "", "5th": "", "6th": ""}
    data_6d = {"draw_date": "", "draw_no": "", "type": "6d", "1st": "", "2nd": {"main": "", "alt": ""}, "3rd": {"main": "", "alt": ""}, "4th": {"main": "", "alt": ""}, "5th": {"main": "", "alt": ""}}
    data_lotto = {"draw_date": "", "draw_no": "", "type": "lotto", "star": [], "power": [], "supreme": [], "jackpots": []}

    toto_texts = soup.find_all(string=re.compile(r"Sports\s*Toto", re.IGNORECASE))
    if not toto_texts:
        print("⚠️ 未找到包含 'Sports Toto' 的文本")
        return None, None, None

    for text_node in toto_texts:
        table = text_node.find_parent("table")
        if table:
            print(f"✅ 找到包含 Sports Toto 的表格")
            header_row = table.find("tr")
            if header_row:
                header_text = header_row.get_text(" ", strip=True)
                date_match = re.search(r"(\d{2}-\d{2}-\d{4})", header_text)
                if date_match:
                    data_5d["draw_date"] = data_6d["draw_date"] = data_lotto["draw_date"] = date_match.group(1)
                    print(f"  ✅ 提取到日期: {date_match.group(1)}")
                no_match = re.search(r"Draw No:?\s*(\d+-\d+)", header_text, re.IGNORECASE)
                if no_match:
                    data_5d["draw_no"] = data_6d["draw_no"] = data_lotto["draw_no"] = no_match.group(1)
                    print(f"  ✅ 提取到期号: {no_match.group(1)}")

            header_5d = table.find("td", string=re.compile(r"5D"))
            if header_5d:
                table_5d = header_5d.find_parent("table")
                if table_5d:
                    rows_5d = table_5d.find_all("tr")
                    for row in rows_5d:
                        tds = row.find_all("td")
                        if len(tds) >= 2:
                            label = tds[0].get_text(strip=True).lower()
                            number = tds[1].get_text(strip=True)
                            if "1st" in label:
                                data_5d["1st"] = number
                            elif "2nd" in label:
                                data_5d["2nd"] = number
                            elif "3rd" in label:
                                data_5d["3rd"] = number
                            elif "4th" in label:
                                data_5d["4th"] = number
                            elif "5th" in label:
                                data_5d["5th"] = number
                            elif "6th" in label:
                                data_5d["6th"] = number
                    print(f"  ✅ 提取到 5D: {data_5d['1st']}, {data_5d['2nd']}, {data_5d['3rd']} ...")

            header_6d = table.find("td", string=re.compile(r"6D"))
            if header_6d:
                table_6d = header_6d.find_parent("table")
                if table_6d:
                    rows_6d = table_6d.find_all("tr")
                    for row in rows_6d:
                        row_text = row.get_text()
                        tds = row.find_all("td")
                        if len(tds) < 2:
                            continue
                        label = tds[0].get_text(strip=True).lower()
                        if "1st" in label and len(tds) >= 2:
                            data_6d["1st"] = tds[1].get_text(strip=True)
                        elif "2nd" in label:
                            main, alt = extract_6d_pair(row_text)
                            data_6d["2nd"]["main"] = main
                            data_6d["2nd"]["alt"] = alt
                        elif "3rd" in label:
                            main, alt = extract_6d_pair(row_text)
                            data_6d["3rd"]["main"] = main
                            data_6d["3rd"]["alt"] = alt
                        elif "4th" in label:
                            main, alt = extract_6d_pair(row_text)
                            data_6d["4th"]["main"] = main
                            data_6d["4th"]["alt"] = alt
                        elif "5th" in label:
                            main, alt = extract_6d_pair(row_text)
                            data_6d["5th"]["main"] = main
                            data_6d["5th"]["alt"] = alt
                    print(f"  ✅ 提取到 6D: 1st {data_6d['1st']}")

            header_lotto = table.find("td", string=re.compile(r"Star Toto 6/50"))
            if header_lotto:
                table_lotto = header_lotto.find_parent("table")
                if table_lotto:
                    rows_lotto = table_lotto.find_all("tr")
                    if len(rows_lotto) >= 2:
                        num_row = rows_lotto[1]
                        tds = num_row.find_all("td")
                        for td in tds:
                            text = td.get_text(strip=True)
                            if text.isdigit():
                                data_lotto["star"].append(text)
                        print(f"  ✅ 提取到 Star Toto 号码: {data_lotto['star']}")

            if any(data_5d.get(k) for k in ['1st','2nd','3rd','4th','5th','6th']) or \
               data_6d.get('1st') or data_lotto.get('star'):
                return data_5d, data_6d, data_lotto

    print("⚠️ 未能从任何包含 'Sports Toto' 的表格中提取到数据")
    return None, None, None

# ---------- 从 4d2ulive.com 获取 Grand Dragon 数据 ----------
def fetch_grand_dragon_from_4d2ulive():
    print("🔍 正在从 4d2ulive.com 获取 Grand Dragon 4D 数据...")
    html = fetch_html(URL_4D2ULIVE)
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    data = {"draw_date": "", "draw_no": "", "1st": "", "2nd": "", "3rd": "", "special": [], "consolation": [], "jackpot": ""}

    header = soup.find(string=re.compile(r"Grand\s+Dragon.*4D.*豪龙", re.IGNORECASE))
    if not header:
        print("⚠️ 未找到 Grand Dragon 标题")
        return None

    header_text = header.get_text(" ", strip=True)
    date_match = re.search(r"(\d{2}-\d{2}-\d{4})", header_text)
    if date_match:
        data["draw_date"] = date_match.group(1)
        print(f"  ✅ 提取到日期: {data['draw_date']}")

    table = header.find_parent("table")
    if not table:
        table = header.find_next("table")
    if not table:
        print("⚠️ 未找到 Grand Dragon 数据表格")
        return None

    rows = table.find_all("tr")
    special_list = []
    cons_list = []
    for row in rows:
        row_text = row.get_text()
        cells = row.find_all("td")
        if "Special" in row_text or "特別獎" in row_text:
            for cell in cells:
                text = cell.get_text(strip=True)
                if text.isdigit() and len(text) == 4:
                    special_list.append(text)
        elif "Consolation" in row_text or "安慰獎" in row_text:
            for cell in cells:
                text = cell.get_text(strip=True)
                if text.isdigit() and len(text) == 4:
                    cons_list.append(text)
        else:
            if len(cells) >= 3:
                data["1st"] = cells[0].get_text(strip=True)
                data["2nd"] = cells[1].get_text(strip=True)
                data["3rd"] = cells[2].get_text(strip=True)

    data["special"] = special_list
    data["consolation"] = cons_list
    return data

# ---------- 保存 JSON 和索引，并存储到数据库 ----------
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

    # ---------- 将号码存入数据库 ----------
    store_numbers_from_data(company, data)

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
    print("🚀 爬虫开始运行")

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
            (re.compile(r'MAGNUM.*JACKPOT.*GOLD', re.I), 'magnum_jackpot_gold', extract_grand_dragon),
            (re.compile(r'MAGNUM.*LIFE', re.I), 'magnum_life', extract_grand_dragon),
        ]

        processed_companies = set()
        for idx, box in enumerate(outer_boxes):
            box_text = box.get_text(" ", strip=True)
            matched = False
            for pattern, company_key, extract_func in company_matchers:
                if pattern.search(box_text):
                    print(f"🔍 处理 {company_key} (outerbox {idx})")
                    data = extract_func(box, global_date, global_draw_no)
                    if data:
                        save_json(company_key, data)
                    processed_companies.add(company_key)
                    matched = True
                    break
            if not matched:
                if "SPORTSTOTO" in box_text.upper():
                    print(f"🔍 尝试提取 SportsToto 复合数据 (outerbox {idx})")
                    data_5d = extract_sportstoto_5d(box, global_date, global_draw_no)
                    if any(data_5d.get(k) for k in ['1st','2nd','3rd','4th','5th','6th']):
                        save_json('sportstoto_5d', data_5d)
                        processed_companies.add('sportstoto_5d')
                    data_6d = extract_sportstoto_6d(box, global_date, global_draw_no)
                    if data_6d.get('1st') or any(data_6d.get(k, {}).get('main') for k in ['2nd','3rd','4th','5th']):
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

    # 2. 从 4dlatest.org 抓取补充数据
    print("\n🌕 正在从 4dlatest.org 抓取补充数据...")
    time.sleep(1)
    html_4dlatest = fetch_html(URL_4DLATEST)
    if html_4dlatest:
        soup_4dlatest = BeautifulSoup(html_4dlatest, "html.parser")

        # 2.1 GDLOTTO 豪龙 (使用最终修复版)
        gd_data = extract_gd_lotto_from_4dlatest(soup_4dlatest)
        if gd_data and (gd_data.get('1st') or gd_data.get('special') or gd_data.get('consolation')):
            # 尝试从4d2ulive补充日期（如果4dlatest没有提取到）
            if not gd_data.get('draw_date'):
                gd_from_4d2u = fetch_grand_dragon_from_4d2ulive()
                if gd_from_4d2u and gd_from_4d2u.get('draw_date'):
                    gd_data['draw_date'] = gd_from_4d2u['draw_date']
                    print(f"  ✅ 从 4d2ulive 补充日期: {gd_from_4d2u['draw_date']}")
            save_json('grand_dragon', gd_data)
        else:
            print("⚠️ GDLOTTO 豪龙数据为空，保留原有数据")

        # 2.2 SABAH88 沙巴万字 LOTTO
        sabah_data = extract_sabah_lotto_from_4dlatest(soup_4dlatest)
        if sabah_data and sabah_data.get('winning_numbers'):
            save_json('sabah_lotto', sabah_data)
        else:
            print("⚠️ SABAH88 沙巴万字 LOTTO 数据为空")

        # 2.3 MAGNUM JACKPOT GOLD
        mjg_data = extract_magnum_jackpot_gold_from_4dlatest(soup_4dlatest)
        if mjg_data and (mjg_data.get('groups') or mjg_data.get('jackpots')):
            save_json('magnum_jackpot_gold', mjg_data)
        else:
            print("⚠️ MAGNUM JACKPOT GOLD 数据为空")

        # 2.4 MAGNUM LIFE
        magnum_life_data = extract_magnum_life_from_4dlatest(soup_4dlatest)
        if magnum_life_data and (magnum_life_data.get('winning_numbers') or magnum_life_data.get('bonus_numbers')):
            save_json('magnum_life', magnum_life_data)
        else:
            print("⚠️ MAGNUM LIFE 数据为空")

        # 2.5 Sports Toto 5D/6D/Lotto
        toto_5d, toto_6d, toto_lotto = extract_sportstoto_from_4dlatest(soup_4dlatest)
        if toto_5d and any(toto_5d.get(k) for k in ['1st','2nd','3rd','4th','5th','6th']):
            save_json('sportstoto_5d', toto_5d)
        if toto_6d and (toto_6d.get('1st') or any(toto_6d.get(k, {}).get('main') for k in ['2nd','3rd','4th','5th'])):
            save_json('sportstoto_6d', toto_6d)
        if toto_lotto and toto_lotto.get('star'):
            save_json('sportstoto_lotto', toto_lotto)

    else:
        print("❌ 无法获取 4dlatest.org 页面")

    # 3. 新加坡 4D & TOTO (从 4dmoon.com)
    print("\n🌕 正在从 4dmoon.com 获取最新新加坡 4D 和 TOTO 数据...")
    time.sleep(1)
    sg_4d, sg_toto = fetch_singapore_from_4dmoon()
    if sg_4d and (sg_4d.get('draw_date') or sg_4d.get('1st')):
        save_json('singapore', sg_4d)  # 注意：公司键是 'singapore' 而不是 'singapore_4d'
    else:
        print("⚠️ 新加坡 4D 数据为空")
    if sg_toto and (sg_toto.get('draw_date') or sg_toto.get('winning_numbers')):
        save_json('singapore_toto', sg_toto)
    else:
        print("⚠️ 新加坡 TOTO 数据为空")

    update_dates_index()

if __name__ == "__main__":
    main()