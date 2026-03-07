import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import re
import time
from urllib.parse import urljoin

# ---------- 配置 ----------
URL_4D4D = "https://4d4d.co/"
URL_4DLATEST = "https://4dlatest.org/"

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

# ---------- 5D 和 6D 提取（增强版） ----------
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
        # 提取所有非空数字
        numbers = []
        for td in tds:
            text = td.get_text(strip=True)
            if text.isdigit() and len(text) >= 2:
                numbers.append(text)
        # 5D 通常每行有 2 或 4 个数字，成对出现
        if len(numbers) >= 2:
            # 尝试按顺序配对
            for i in range(0, len(numbers), 2):
                if i+1 < len(numbers):
                    label = f"第{len(data)+1}组"  # 或者根据上下文推测
                    # 如果能从前面单元格获取标签更好，但这里简化
                    data.append([label, numbers[i], numbers[i+1] if i+1 < len(numbers) else ''])
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
        # 提取数字，忽略 "or"
        numbers = []
        for td in tds:
            text = td.get_text(strip=True)
            if text.isdigit() and len(text) >= 2:
                numbers.append(text)
        # 6D 可能一行有多个数字，例如排名、主号码、备选号码
        if numbers:
            # 第一个通常是排名，后续是号码
            rank = numbers[0]
            main_num = numbers[1] if len(numbers) > 1 else ''
            alt_num = numbers[2] if len(numbers) > 2 else ''
            data.append([rank, main_num, alt_num])
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

# ---------- 乐透提取 ----------
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

# ---------- 从 4dlatest.org 提取 GDLOTTO ----------
def extract_gd_lotto_from_4dlatest(soup):
    print("🔍 正在从 4dlatest.org 提取 GDLOTTO 豪龙数据...")
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
    header = soup.find(string=re.compile(r"GDLOTTO 豪龙"))
    if not header:
        print("⚠️ 未找到 'GDLOTTO 豪龙' 标题")
        return None
    table = header.find_parent("table")
    if not table:
        table = header.find_next("table")
    if not table:
        print("⚠️ 未找到 GDLOTTO 数据表格")
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
    no_match = re.search(r"#?(\d+/\d+)", header_text)
    if no_match:
        data["draw_no"] = no_match.group(1)
        print(f"  提取到期号: {data['draw_no']}")
    rows = table.find_all("tr")
    special_mode = False
    consolation_mode = False
    special_list = []
    consolation_list = []
    for row in rows:
        row_text = row.get_text().upper()
        cells = row.find_all("td")
        if "SPECIAL" in row_text:
            special_mode = True
            consolation_mode = False
            for cell in cells:
                text = cell.get_text(strip=True)
                if text.isdigit() and len(text) >= 3:
                    special_list.append(text)
            continue
        if "CONSOLATION" in row_text:
            special_mode = False
            consolation_mode = True
            for cell in cells:
                text = cell.get_text(strip=True)
                if text.isdigit() and len(text) >= 3:
                    consolation_list.append(text)
            continue
        if "JACKPOT" in row_text or "USD" in row_text or "$" in row_text:
            amount_match = re.search(r'([\d,]+(?:\.\d+)?)', row.get_text())
            if amount_match:
                data["jackpot"] = amount_match.group(1)
            continue
        if special_mode:
            for cell in cells:
                text = cell.get_text(strip=True)
                if text.isdigit() and len(text) >= 3:
                    special_list.append(text)
        if consolation_mode:
            for cell in cells:
                text = cell.get_text(strip=True)
                if text.isdigit() and len(text) >= 3:
                    consolation_list.append(text)
        if "1ST" in row_text:
            for cell in cells:
                text = cell.get_text(strip=True)
                if text.isdigit() and len(text) >= 3:
                    data["1st"] = text
                    break
        if "2ND" in row_text:
            for cell in cells:
                text = cell.get_text(strip=True)
                if text.isdigit() and len(text) >= 3:
                    data["2nd"] = text
                    break
        if "3RD" in row_text:
            for cell in cells:
                text = cell.get_text(strip=True)
                if text.isdigit() and len(text) >= 3:
                    data["3rd"] = text
                    break
    data["special"] = list(dict.fromkeys(special_list))[:10]
    data["consolation"] = list(dict.fromkeys(consolation_list))[:10]
    print(f"  提取到前三: {data['1st']}, {data['2nd']}, {data['3rd']}")
    print(f"  特别奖数量: {len(data['special'])}")
    print(f"  安慰奖数量: {len(data['consolation'])}")
    print(f"  Jackpot: {data['jackpot']}")
    return data

# ---------- 从 4dlatest.org 提取 SABAH88 LOTTO（增强版） ----------
def extract_sabah_lotto_from_4dlatest(soup):
    print("🔍 正在从 4dlatest.org 提取 SABAH88 沙巴万字 LOTTO 数据...")
    data = {
        "draw_date": "",
        "draw_no": "",
        "winning_numbers": [],
        "jackpot1": "",
        "jackpot2": ""
    }
    # 更宽松的标题匹配
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
            continue
        if "Jackpot 1" in row_text:
            for cell in cells:
                text = cell.get_text(strip=True)
                amount_match = re.search(r'([\d,]+(?:\.\d+)?)', text)
                if amount_match:
                    data["jackpot1"] = amount_match.group(1)
                    print(f"  ✅ Jackpot 1: {data['jackpot1']}")
                    break
            if not data["jackpot1"]:
                next_row = row.find_next_sibling("tr")
                if next_row:
                    next_cells = next_row.find_all("td")
                    for cell in next_cells:
                        text = cell.get_text(strip=True)
                        amount_match = re.search(r'([\d,]+(?:\.\d+)?)', text)
                        if amount_match:
                            data["jackpot1"] = amount_match.group(1)
                            print(f"  ✅ Jackpot 1 (下一行): {data['jackpot1']}")
                            break
        if "Jackpot 2" in row_text:
            for cell in cells:
                text = cell.get_text(strip=True)
                amount_match = re.search(r'([\d,]+(?:\.\d+)?)', text)
                if amount_match:
                    data["jackpot2"] = amount_match.group(1)
                    print(f"  ✅ Jackpot 2: {data['jackpot2']}")
                    break
            if not data["jackpot2"]:
                next_row = row.find_next_sibling("tr")
                if next_row:
                    next_cells = next_row.find_all("td")
                    for cell in next_cells:
                        text = cell.get_text(strip=True)
                        amount_match = re.search(r'([\d,]+(?:\.\d+)?)', text)
                        if amount_match:
                            data["jackpot2"] = amount_match.group(1)
                            print(f"  ✅ Jackpot 2 (下一行): {data['jackpot2']}")
                            break
    return data

# ---------- 从 Singapore Pools 获取 TOTO ----------
def fetch_singapore_toto_from_official():
    print("🔍 正在从 Singapore Pools 官方获取最新 TOTO 数据...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    main_url = "https://www.singaporepools.com.sg/en/product/Pages/toto_results.aspx"
    try:
        r = requests.get(main_url, headers=headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        latest_link = None
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'toto_results.aspx' in href and 'sppl=' in href:
                latest_link = urljoin(main_url, href)
                print(f"✅ 找到最新结果链接: {latest_link}")
                break
        if not latest_link:
            print("❌ 未找到最新结果链接")
            return None
        r2 = requests.get(latest_link, headers=headers, timeout=15)
        r2.raise_for_status()
        soup2 = BeautifulSoup(r2.text, "html.parser")
        data = {"draw_date": "", "draw_no": "", "winning_numbers": [], "prize_table": []}
        header = soup2.find('h2', string=re.compile(r'TOTO Results', re.I))
        if header:
            header_text = header.get_text()
            date_match = re.search(r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})', header_text)
            if date_match:
                try:
                    d = datetime.strptime(date_match.group(1), "%d %b %Y")
                    data["draw_date"] = d.strftime("%d-%m-%Y")
                except:
                    pass
            no_match = re.search(r'Draw\s*No\.?\s*(\d+)', header_text, re.I)
            if no_match:
                data["draw_no"] = no_match.group(1)
        winning_section = soup2.find('span', string=re.compile(r'Winning Numbers', re.I))
        if winning_section:
            table = winning_section.find_parent('table')
            if table:
                numbers = []
                for td in table.find_all('td'):
                    text = td.get_text(strip=True)
                    if text.isdigit() and 1 <= int(text) <= 49:
                        numbers.append(text)
                if len(numbers) >= 7:
                    data["winning_numbers"] = numbers[:6] + [numbers[-1]]
                elif numbers:
                    data["winning_numbers"] = numbers
        prize_header = soup2.find('th', string=re.compile(r'Prize Group', re.I))
        if prize_header:
            table = prize_header.find_parent('table')
            if table:
                rows = table.find_all('tr')[1:]
                prize_table = []
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        group = cells[0].get_text(strip=True)
                        amount = cells[1].get_text(strip=True)
                        winners = cells[2].get_text(strip=True)
                        prize_table.append([group, amount, winners])
                data["prize_table"] = prize_table
        if data["winning_numbers"] and len(data["prize_table"]) >= 6:
            print(f"✅ 成功获取 TOTO 数据: 期号 {data['draw_no']}")
            return data
        else:
            print("⚠️ 获取的数据不完整")
            return None
    except Exception as e:
        print(f"❌ 抓取失败: {e}")
        return None

# ---------- 新增：从 4d4d.co 提取 Magnum Jackpot Gold ----------
def extract_magnum_jackpot_gold(box, global_date, global_draw_no):
    data = base_extract(box, global_date, global_draw_no)
    # 尝试提取 jackpot 表格
    # 通常 Jackpot Gold 会有特殊的表格结构，包含 GROUP 1, GROUP 2 等
    # 我们简单提取所有包含 "Jackpot" 的行中的金额
    jackpot_table = box.find("table", string=re.compile(r"Jackpot", re.I))
    if jackpot_table:
        rows = jackpot_table.find_all("tr")
        jackpot_data = []
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True)
                amount = cells[1].get_text(strip=True)
                jackpot_data.append([label, amount])
        data['jackpot_data'] = jackpot_data
    return data

# ---------- 新增：从 4d4d.co 提取 Magnum Life ----------
def extract_magnum_life(box, global_date, global_draw_no):
    data = base_extract(box, global_date, global_draw_no)
    # Magnum Life 可能是 6/50 类型的彩票，提取 winning numbers 和 bonus numbers
    winning_section = box.find("td", string=re.compile(r"WINNING NUMBERS", re.I))
    if winning_section:
        table = winning_section.find_parent("table")
        if table:
            rows = table.find_all("tr")
            # 假设号码在第二行
            if len(rows) >= 2:
                cells = rows[1].find_all("td")
                data['winning_numbers'] = [c.get_text(strip=True) for c in cells if c.get_text(strip=True).isdigit()]
            # 查找 BONUS NUMBERS
            bonus_section = box.find("td", string=re.compile(r"BONUS NUMBERS", re.I))
            if bonus_section:
                bonus_row = bonus_section.find_parent("tr")
                if bonus_row:
                    cells = bonus_row.find_all("td")[1:]  # 跳过标签
                    data['bonus_numbers'] = [c.get_text(strip=True) for c in cells if c.get_text(strip=True).isdigit()]
    return data

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
            (re.compile(r'MAGNUM.*JACKPOT.*GOLD', re.I), 'magnum_jackpot_gold', extract_magnum_jackpot_gold),
            (re.compile(r'MAGNUM.*LIFE', re.I), 'magnum_life', extract_magnum_life),
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
                        print(f"  提取到 {len(data['data'])} 条数据")
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

    # 2. 从 4dlatest.org 抓取 GDLOTTO 和 SABAH LOTTO
    print("\n🌕 正在从 4dlatest.org 抓取补充数据...")
    time.sleep(1)
    html_4dlatest = fetch_html(URL_4DLATEST)
    if html_4dlatest:
        soup_4dlatest = BeautifulSoup(html_4dlatest, "html.parser")
        gd_data = extract_gd_lotto_from_4dlatest(soup_4dlatest)
        if gd_data and gd_data.get('1st'):
            save_json('grand_dragon', gd_data)
        else:
            print("⚠️ GDLOTTO 豪龙数据为空，保留原有数据")
        sabah_data = extract_sabah_lotto_from_4dlatest(soup_4dlatest)
        if sabah_data and sabah_data.get('winning_numbers'):
            save_json('sabah_lotto', sabah_data)
        else:
            print("⚠️ SABAH88 沙巴万字 LOTTO 数据为空")
    else:
        print("❌ 无法获取 4dlatest.org 页面")

    # 3. 从 Singapore Pools 获取 TOTO
    print("\n🌕 正在从官方获取最新 Singapore TOTO 数据...")
    time.sleep(1)
    toto_data = fetch_singapore_toto_from_official()
    if toto_data and toto_data.get('winning_numbers'):
        save_json('singapore_toto', toto_data)
    else:
        print("⚠️ Singapore TOTO 数据为空")

    update_dates_index()

if __name__ == "__main__":
    main()