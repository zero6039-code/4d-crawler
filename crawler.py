import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import re
import time
import sqlite3
import subprocess
from urllib.parse import urljoin

# ========== 路径统一配置 ==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '4d_results.db')

# ---------- 配置 ----------
URL_4D4D = "https://4d4d.co/"
URL_4DLATEST = "https://4dlatest.org/"
URL_4D2ULIVE = "https://4d2ulive.com"

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
        if num and num != '----':
            insert_number(company, field, num, draw_date)
    
    for field in list_fields:
        nums = data.get(field, [])
        if isinstance(nums, list):
            for num in nums:
                if num and num != '----':
                    insert_number(company, field, num, draw_date)
    
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
    
    if company == 'magnum_jackpot_gold':
        groups = data.get('groups', [])
        for grp in groups:
            grp_num = grp.get('group')
            nums = grp.get('numbers', [])
            for num in nums:
                if num and num != '+':
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

# ================== 修复 extract_sportstoto_from_4dlatest 函数 ==================
def extract_sportstoto_from_4dlatest(soup):
    """提取 Sports Toto 5D/6D/Lotto 数据，确保始终返回三个值"""
    print("🔍 正在从 4dlatest.org 提取 Sports Toto 5D/6D/Lotto 数据...")
    data_5d = {"draw_date": "", "draw_no": "", "type": "5d", "1st": "", "2nd": "", "3rd": "", "4th": "", "5th": "", "6th": ""}
    data_6d = {"draw_date": "", "draw_no": "", "type": "6d", "1st": "", "2nd": {"main": "", "alt": ""}, "3rd": {"main": "", "alt": ""}, "4th": {"main": "", "alt": ""}, "5th": {"main": "", "alt": ""}}
    data_lotto = {"draw_date": "", "draw_no": "", "type": "lotto", "star": [], "power": [], "supreme": [], "jackpots": []}

    toto_texts = soup.find_all(string=re.compile(r"Sports\s*Toto", re.IGNORECASE))
    if not toto_texts:
        print("⚠️ 未找到包含 'Sports Toto' 的文本")
        return data_5d, data_6d, data_lotto  # 返回空数据，而不是 None

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
    return data_5d, data_6d, data_lotto  # 始终返回三个空字典

# ================== 从 dato4d.com JSON 抓取 Grand Dragon 数据 ==================
def fetch_grand_dragon_from_dato4d_json():
    print("🔍 正在从 dato4d.com JSON 获取 Grand Dragon 4D 数据...")
    url = "https://www.dato4d.com/liveos.json?_=" + str(int(time.time()*1000))
    html = fetch_html(url)
    if not html:
        return None

    try:
        data = json.loads(html)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        return None

    if "G" not in data:
        print("⚠️ JSON 中未找到 Grand Dragon 数据 (键 'G')")
        return None

    g = data["G"]
    result = {
        "draw_date": "",
        "draw_no": g.get("DN", ""),
        "1st": g.get("P1", ""),
        "2nd": g.get("P2", ""),
        "3rd": g.get("P3", ""),
        "special": [],
        "consolation": [],
        "jackpot": ""
    }

    raw_date = g.get("DD", "")
    date_match = re.search(r"(\d{2}-\d{2}-\d{4})", raw_date)
    if date_match:
        result["draw_date"] = date_match.group(1)
        print(f"  ✅ 提取到日期: {result['draw_date']}")

    for i in range(1, 14):
        key = f"S{i}"
        if key in g:
            num = g[key]
            if num and num != "----":
                result["special"].append(num)
    print(f"  ✅ 特别奖数量: {len(result['special'])}")

    for i in range(1, 11):
        key = f"C{i}"
        if key in g:
            num = g[key]
            if num and num != "----":
                result["consolation"].append(num)
    print(f"  ✅ 安慰奖数量: {len(result['consolation'])}")

    if result["draw_date"] and (result["1st"] or result["special"]):
        print(f"✅ 成功从 JSON 提取 Grand Dragon 数据，日期 {result['draw_date']}")
        return result
    else:
        print("⚠️ JSON 中 Grand Dragon 数据不完整")
        return None

# ================== 原有从 gdlotto.net 抓取 Grand Dragon 函数 ==================
def fetch_grand_dragon_from_gdlotto_net():
    # ... 保持不变，省略以节省篇幅，实际使用时请保留 ...
    pass

# ================== 原有其他补充源函数 ==================
def fetch_singapore_from_4dmoon():
    # ... 保持不变 ...
    pass

def extract_gd_lotto_from_4dlatest(soup):
    # ... 保持不变 ...
    pass

def extract_sabah_lotto_from_4dlatest(soup):
    # ... 保持不变 ...
    pass

def extract_magnum_jackpot_gold_from_4dlatest(soup):
    # ... 保持不变 ...
    pass

def extract_magnum_life_from_4dlatest(soup):
    # ... 保持不变 ...
    pass

def fetch_sabah_lotto_from_4dmoon():
    # ... 保持不变 ...
    pass

def fetch_sportstoto_5d_6d_from_4dmoon():
    # ... 保持不变 ...
    pass

def fetch_grand_dragon_from_4d2ulive():
    # ... 保持不变 ...
    pass

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

# ================== Git 推送函数 ==================
def git_push_to_github():
    """将生成的 JSON 文件提交并推送到 GitHub 仓库"""
    print("📤 正在推送更新到 GitHub...")
    try:
        # 配置 Git 用户信息
        subprocess.run(['git', 'config', 'user.name', 'github-actions[bot]'], 
                       check=False, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'github-actions[bot]@users.noreply.github.com'], 
                       check=False, capture_output=True)
        
        # 添加所有变更
        add_result = subprocess.run(['git', 'add', 'docs/data/'], 
                                    check=False, capture_output=True, text=True)
        if add_result.returncode != 0:
            print(f"⚠️ git add 失败: {add_result.stderr}")
            return
        
        # 检查是否有变更
        status_result = subprocess.run(['git', 'status', '--porcelain'], 
                                       check=False, capture_output=True, text=True)
        if not status_result.stdout.strip():
            print("ℹ️ 没有文件变更，无需提交")
            return
        
        # 提交
        commit_msg = f"Auto-update 4D results {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        commit_result = subprocess.run(['git', 'commit', '-m', commit_msg], 
                                       check=False, capture_output=True, text=True)
        if commit_result.returncode != 0:
            print(f"⚠️ git commit 失败: {commit_result.stderr}")
            return
        
        # 获取 token 并推送
        token = os.environ.get('GITHUB_TOKEN')
        if not token:
            print("⚠️ 未设置 GITHUB_TOKEN 环境变量，跳过推送")
            return
        
        remote_url = subprocess.run(['git', 'config', '--get', 'remote.origin.url'], 
                                    check=False, capture_output=True, text=True).stdout.strip()
        if 'https://' in remote_url:
            auth_url = remote_url.replace('https://', f'https://{token}@')
        else:
            print("⚠️ 远程仓库不是 HTTPS 协议，无法使用 token 推送")
            return
        
        push_result = subprocess.run(['git', 'push', auth_url], 
                                     check=False, capture_output=True, text=True)
        if push_result.returncode == 0:
            print("✅ 成功推送更新到 GitHub")
        else:
            print(f"❌ git push 失败: {push_result.stderr}")
            
    except Exception as e:
        print(f"⚠️ Git 操作异常: {e}")

# ---------- 主流程（带错误保护）----------
def main():
    print("🚀 爬虫开始运行")
    try:
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

            # 2.1 GDLOTTO 豪龙 - 优先使用 dato4d.com JSON
            gd_data = fetch_grand_dragon_from_dato4d_json()
            if not gd_data:
                print("⚠️ dato4d.com JSON 抓取失败，尝试从 gdlotto.net 获取...")
                gd_data = fetch_grand_dragon_from_gdlotto_net()
            if not gd_data:
                print("⚠️ gdlotto.net 抓取失败，尝试从 4dlatest.org 获取...")
                gd_data = extract_gd_lotto_from_4dlatest(soup_4dlatest)
            
            if gd_data and (gd_data.get('1st') or gd_data.get('special') or gd_data.get('consolation')):
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

            # 2.5 Sports Toto 5D/6D/Lotto（使用修复后的函数）
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
            save_json('singapore', sg_4d)
        else:
            print("⚠️ 新加坡 4D 数据为空")
        if sg_toto and (sg_toto.get('draw_date') or sg_toto.get('winning_numbers')):
            save_json('singapore_toto', sg_toto)
        else:
            print("⚠️ 新加坡 TOTO 数据为空")

        # 4. 从 4dmoon.com 补充 Sabah Lotto 和 Sports Toto 5D/6D
        print("\n🌕 正在从 4dmoon.com 补充 Sabah Lotto 和 Sports Toto 5D/6D 数据...")
        time.sleep(1)
        sabah_lotto_4dmoon = fetch_sabah_lotto_from_4dmoon()
        if sabah_lotto_4dmoon:
            save_json('sabah_lotto', sabah_lotto_4dmoon)

        toto_5d_4dmoon, toto_6d_4dmoon = fetch_sportstoto_5d_6d_from_4dmoon()
        if toto_5d_4dmoon and any(toto_5d_4dmoon.get(k) for k in ['1st','2nd','3rd','4th','5th','6th']):
            save_json('sportstoto_5d', toto_5d_4dmoon)
        if toto_6d_4dmoon and (toto_6d_4dmoon.get('1st') or any(toto_6d_4dmoon.get(k, {}).get('main') for k in ['2nd','3rd','4th','5th'])):
            save_json('sportstoto_6d', toto_6d_4dmoon)

        update_dates_index()

    except Exception as e:
        print(f"❌ 爬虫运行过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔚 爬虫执行完毕，尝试推送更新到 GitHub...")
        # 即使有错误也尝试推送（因为可能部分数据已保存）
        git_push_to_github()

if __name__ == "__main__":
    main()
