import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import re
import time
import sqlite3
from urllib.parse import urljoin

# ========== 路径统一配置 ==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '4d_results.db')

# ---------- 配置 ----------
URL_4D4D = "https://4d4d.co/"
URL_DATO4D = "https://www.dato4d.com/liveos.json"

# ---------- 日期转换辅助函数 ----------
def dmy_to_ymd(date_str):
    if not date_str or date_str == '----':
        return None
    try:
        d = datetime.strptime(date_str, "%d-%m-%Y")
        return d.strftime("%Y-%m-%d")
    except:
        return None

def ymd_to_dmy(date_str):
    if not date_str:
        return ''
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return d.strftime("%d-%m-%Y")
    except:
        return date_str

# ---------- 数据库辅助函数 ----------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            type TEXT NOT NULL,
            number TEXT NOT NULL,
            draw_date TEXT NOT NULL,
            UNIQUE(company, type, number, draw_date)
        )
    ''')
    conn.commit()
    return conn

def insert_number(company, type_, number, draw_date):
    if not number or number == '----':
        return
    conn = get_db_connection()
    c = conn.cursor()
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
    raw_date = data.get('draw_date')
    draw_date = dmy_to_ymd(raw_date) if raw_date else datetime.now().strftime("%Y-%m-%d")
    if not draw_date:
        draw_date = datetime.now().strftime("%Y-%m-%d")

    prize_fields = ['1st', '2nd', '3rd']
    list_fields = ['special', 'consolation', 'winning_numbers', 'star', 'power', 'supreme']
    
    for field in prize_fields:
        num = data.get(field)
        if num and isinstance(num, str) and num != '----':
            insert_number(company, field, num, draw_date)
    
    for field in list_fields:
        nums = data.get(field, [])
        if isinstance(nums, list):
            for num in nums:
                if num and isinstance(num, str) and num != '----':
                    insert_number(company, field, num, draw_date)
    
    if company == 'sportstoto_6d':
        for pos in ['2nd', '3rd', '4th', '5th']:
            item = data.get(pos, {})
            if isinstance(item, dict):
                main = item.get('main')
                alt = item.get('alt')
                if main and isinstance(main, str) and main != '----':
                    insert_number(company, f'{pos}_main', main, draw_date)
                if alt and isinstance(alt, str) and alt != '----':
                    insert_number(company, f'{pos}_alt', alt, draw_date)
    
    if company == 'magnum_jackpot_gold':
        groups = data.get('groups', [])
        for grp in groups:
            grp_num = grp.get('group')
            nums = grp.get('numbers', [])
            for num in nums:
                if num and isinstance(num, str) and num != '+':
                    insert_number(company, f'group_{grp_num}', num, draw_date)

# ---------- 增强版请求函数（支持重试、会话、完整头）----------
def fetch_html(url, max_retries=3, timeout=15):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://gdlotto.net/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    if "gdlotto.net" in url:
        try:
            print("🌐 先访问 gdlotto.net 首页以获取 cookies...")
            session.get("https://gdlotto.net/", timeout=timeout)
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ 访问首页失败，但仍尝试请求目标URL: {e}")

    for attempt in range(max_retries):
        try:
            print(f"🌐 正在请求 {url} (尝试 {attempt+1}/{max_retries})")
            r = session.get(url, timeout=timeout)
            print(f"  状态码: {r.status_code}")
            print(f"  内容长度: {len(r.text)}")
            preview = r.text[:500].replace('\n', ' ').replace('\r', '')
            print(f"  内容预览: {preview}...")
            r.encoding = "utf-8"
            r.raise_for_status()
            return r.text
        except requests.exceptions.RequestException as e:
            print(f"❌ 抓取失败: {e}")
            if attempt < max_retries - 1:
                print(f"⏳ 等待 {attempt+1} 秒后重试...")
                time.sleep(attempt + 1)
            else:
                return None
    return None

def find_parent_table(element):
    while element and element.name != 'table':
        element = element.parent
    return element

def parse_4dmoon_date(date_str):
    try:
        d = datetime.strptime(date_str.strip(), "%d-%b-%Y")
        return d.strftime("%d-%m-%Y")
    except:
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
    # 如果有 Life 相关字段，可以在这里扩展
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

    # 1+3D 的特别奖和安慰奖是 6 位数字，直接提取
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
    # 提取 3D
    result['3d'] = {
        "1st": item.get("P13D", ""),
        "2nd": item.get("P23D", ""),
        "3rd": item.get("P33D", "")
    }
    return result

def extract_grand_dragon_from_json(item, company):
    """提取 Grand Dragon 4D 数据"""
    result = extract_standard_4d_from_json(item, company)
    # Grand Dragon 可能有 Jackpot，但 JSON 中没有，保留为空
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

    # 提取组号码 (P1-P8 可能代表各组号码，需确认)
    groups = []
    for i in range(1, 9):
        key = f"P{i}"
        if key in item and item[key]:
            groups.append({
                "group": str(i),
                "numbers": [item[key]]  # 假设每组只有一个号码
            })
    result["groups"] = groups

    # 提取 Jackpots
    if "JP1" in item:
        result["jackpots"].append(item["JP1"])
    if "JP2" in item:
        result["jackpots"].append(item["JP2"])
    return result

def extract_sabah_lotto_from_json(item, company):
    """提取 Sabah Lotto 数据（包含 Lotto 6/45、Lotto 6 和 Lotto 5 的所有组）"""
    result = {
        "draw_date": extract_date_from_dd(item.get("DD", "")),
        "draw_no": item.get("DN", ""),
        "winning_numbers": [],
        "jackpot1": "",
        "jackpot2": ""
    }

    # 提取 Lotto 6/45 主号码 (LT1-LT7)
    winning = []
    for i in range(1, 8):
        key = f"LT{i}"
        if key in item:
            num = item[key]
            if num:
                winning.append(num)
    result["winning_numbers"] = winning

    # 提取两个主 Jackpot
    if "LTJP1" in item:
        result["jackpot1"] = item["LTJP1"]
    if "LTJP2" in item:
        result["jackpot2"] = item["LTJP2"]

    # ===== 提取 Lotto 6 组数据（共5组） =====
    for g in range(1, 6):  # 组号 1-5
        # 每组6个号码：前5个为普通号码，第6个为额外号
        for i in range(1, 7):
            key = f"LT6G{g}{i}"
            if key in item:
                result[key] = item[key]
        # 对应 Jackpot 奖金
        jp_key = f"LT6G{g}JP"
        if jp_key in item:
            result[jp_key] = item[jp_key]

    # ===== 提取 Lotto 5 组数据（共8组） =====
    for g in range(1, 9):  # 组号 1-8
        # 每组5个号码：前4个为普通号码，第5个为额外号
        for i in range(1, 6):
            key = f"LT5G{g}{i}"
            if key in item:
                result[key] = item[key]
        # 对应 Jackpot 奖金
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

    # 提取开奖号码 (P1-P7)
    winning = []
    for i in range(1, 8):
        key = f"P{i}"
        if key in item:
            num = item[key]
            if num:
                winning.append(num)
    result["winning_numbers"] = winning

    # 提取奖金表 (JP1, JP2 等)
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
    """从 T 对象提取 Sports Toto 5D 数据"""
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
    """从 T 对象提取 Sports Toto 6D 数据"""
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
    """从 T 对象提取 Sports Toto Lotto (Star/Power/Supreme) 数据"""
    # 过滤无效值
    def clean_num(val):
        return val if val and val not in ["-", "----"] else ""

    star = [
        clean_num(t_item.get("P6501")),
        clean_num(t_item.get("P6502")),
        clean_num(t_item.get("P6503")),
        clean_num(t_item.get("P6504")),
        clean_num(t_item.get("P6505")),
        clean_num(t_item.get("P6506")),
        clean_num(t_item.get("P650EX"))
    ]
    power = [
        clean_num(t_item.get("P6551")),
        clean_num(t_item.get("P6552")),
        clean_num(t_item.get("P6553")),
        clean_num(t_item.get("P6554")),
        clean_num(t_item.get("P6555")),
        clean_num(t_item.get("P6556"))
    ]
    supreme = [
        clean_num(t_item.get("P6581")),
        clean_num(t_item.get("P6582")),
        clean_num(t_item.get("P6583")),
        clean_num(t_item.get("P6584")),
        clean_num(t_item.get("P6585")),
        clean_num(t_item.get("P6586"))
    ]
    # 提取 Jackpots: 顺序为 Star JP1, Star JP2, Power JP, Supreme JP
    jackpots = [
        clean_num(t_item.get("P650JP1")),
        clean_num(t_item.get("P650JP2")),
        clean_num(t_item.get("P655JP")),
        clean_num(t_item.get("P658JP"))
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
    """从 M 对象提取 Magnum Life 数据"""
    def clean_num(val):
        return val if val and val not in ["-", "----"] else ""

    winning = [
        clean_num(m_item.get("L1")),
        clean_num(m_item.get("L2")),
        clean_num(m_item.get("L3")),
        clean_num(m_item.get("L4")),
        clean_num(m_item.get("L5")),
        clean_num(m_item.get("L6")),
        clean_num(m_item.get("L7")),
        clean_num(m_item.get("L8"))
    ]
    bonus = [
        clean_num(m_item.get("LB1")),
        clean_num(m_item.get("LB2"))
    ]
    return {
        "draw_date": extract_date_from_dd(m_item.get("DD", "")),
        "draw_no": m_item.get("DN", ""),
        "type": "life",
        "winning_numbers": [n for n in winning if n],
        "bonus_numbers": [n for n in bonus if n]
    }

def fetch_all_companies_from_dato4d():
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
        # Sports Toto 5D
        toto_5d_data = extract_sportstoto_5d_from_json(t_item, "sportstoto_5d")
        if toto_5d_data and any(toto_5d_data.get(k) for k in ['1st','2nd','3rd','4th','5th','6th']):
            save_json("sportstoto_5d", toto_5d_data)
            success_count += 1
        # Sports Toto 6D
        toto_6d_data = extract_sportstoto_6d_from_json(t_item, "sportstoto_6d")
        if toto_6d_data and (toto_6d_data.get('1st') or any(toto_6d_data.get(k, {}).get('main') for k in ['2nd','3rd','4th','5th'])):
            save_json("sportstoto_6d", toto_6d_data)
            success_count += 1
        # Sports Toto Lotto
        toto_lotto_data = extract_sportstoto_lotto_from_json(t_item, "sportstoto_lotto")
        if toto_lotto_data and (toto_lotto_data.get('star') or toto_lotto_data.get('power') or toto_lotto_data.get('supreme')):
            save_json("sportstoto_lotto", toto_lotto_data)
            success_count += 1
    else:
        print("⚠️ JSON 中缺少 T (Toto) 的数据")

    # 额外处理 M 对象中的 Magnum Life
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

# ---------- 保存 JSON 和索引 ----------
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

    raw_date = data.get("draw_date", "")
    if raw_date:
        ymd_date = dmy_to_ymd(raw_date)
        if not ymd_date:
            ymd_date = datetime.now().strftime("%Y-%m-%d")
    else:
        ymd_date = datetime.now().strftime("%Y-%m-%d")
    archive_dir = os.path.join(base_dir, ymd_date)
    os.makedirs(archive_dir, exist_ok=True)
    archive_path = os.path.join(archive_dir, f"{company}.json")
    with open(archive_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"📁 已归档至: {archive_path}")

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

    # 首先尝试从 dato4d.com JSON 批量获取所有数据
    json_success = fetch_all_companies_from_dato4d()

    # 如果 JSON 源失败，则回退到 4d4d.co 抓取（已定义）
    if not json_success:
        print("⚠️ 批量 JSON 获取失败，回退到 4d4d.co 抓取...")
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
        else:
            print("❌ 无法获取 4d4d.co 数据")

    # 更新日期索引
    update_dates_index()
    print("🔚 爬虫执行完毕")

if __name__ == "__main__":
    main()