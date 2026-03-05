import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import re
import time

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

# ---------- 4d4d.co 提取函数 (保持不变) ----------
# ... (此处省略您原有所有从 4d4d.co 抓取的函数，例如 extract_damacai, extract_magnum 等)
# 请确保在最终代码中完整保留您原有的这些函数。
# 为了节省篇幅，此处用注释代替，但您在实际替换时必须保留它们。

def extract_damacai(box, global_date, global_draw_no): return base_extract(box, global_date, global_draw_no)
def extract_magnum(box, global_date, global_draw_no): return base_extract(box, global_date, global_draw_no)
def extract_toto(box, global_date, global_draw_no): return base_extract(box, global_date, global_draw_no)
def extract_singapore(box, global_date, global_draw_no): # ... 函数体
def extract_damacai_1p3d(box, global_date, global_draw_no): return base_extract(box, global_date, global_draw_no)
def extract_sandakan(box, global_date, global_draw_no): return base_extract(box, global_date, global_draw_no)
def extract_cashsweep(box, global_date, global_draw_no): return base_extract(box, global_date, global_draw_no)
def extract_sabah(box, global_date, global_draw_no): # ... 函数体
def extract_sportstoto_5d(box, global_date, global_draw_no): # ... 函数体
def extract_sportstoto_6d(box, global_date, global_draw_no): # ... 函数体
def extract_sportstoto_lotto(box, global_date, global_draw_no): # ... 函数体
def extract_grand_dragon(box, global_date, global_draw_no): return base_extract(box, global_date, global_draw_no)
def base_extract(box, global_date, global_draw_no): # ... 函数体
def extract_3d(box): # ... 函数体
def extract_5d_table(box): # ... 函数体
def extract_6d_table(box): # ... 函数体
def extract_lotto(box): # ... 函数体

# ========== 最终优化版 GDLOTTO 豪龙提取函数 ==========
def extract_gd_lotto_from_4dlatest(soup):
    """
    从 https://4dlatest.org/ 提取 GDLOTTO 豪龙数据
    最终优化：使用合并文本提取日期，支持多种格式
    """
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
        print("⚠️ 未找到 GDLOTTO 数据表格")
        return None

    # 使用空格连接多行文本，避免换行符干扰
    header_text = header.get_text(" ", strip=True)
    print(f"📅 标题文本: {header_text}")

    # --- 增强的日期提取 ---
    date_match = None
    # 尝试匹配 DD/MM/YYYY
    date_match = re.search(r'(\d{2}/\d{2}/\d{4})', header_text)
    if not date_match:
        # 尝试匹配 DD-MM-YYYY
        date_match = re.search(r'(\d{2}-\d{2}-\d{4})', header_text)
    if not date_match:
        # 尝试匹配 DD.MM.YYYY
        date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', header_text)

    if date_match:
        raw_date = date_match.group(1).replace('/', '-').replace('.', '-')
        try:
            # 验证并统一格式
            d = datetime.strptime(raw_date, "%d-%m-%Y")
            data["draw_date"] = d.strftime("%d-%m-%Y")
            print(f"  ✅ 提取到日期: {data['draw_date']}")
        except Exception as e:
            print(f"  ⚠️ 日期解析失败: {e}")
    else:
        print("  ❌ 未找到日期")

    # 提取期号（如果有）
    no_match = re.search(r"#?(\d+/\d+)", header_text)
    if no_match:
        data["draw_no"] = no_match.group(1)
        print(f"  提取到期号: {data['draw_no']}")

    # ... 后续提取逻辑完全不变 ...
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

# ========== 最终优化版 SABAH88 沙巴万字 LOTTO 提取函数 ==========
def extract_sabah_lotto_from_4dlatest(soup):
    """
    从 https://4dlatest.org/ 提取 "SABAH88 沙巴万字 LOTTO" 数据
    最终优化：保留宽松匹配和Jackpot下一行查找逻辑
    """
    print("🔍 正在从 4dlatest.org 提取 SABAH88 沙巴万字 LOTTO 数据...")
    data = {
        "draw_date": "",
        "draw_no": "",
        "winning_numbers": [],
        "jackpot1": "",
        "jackpot2": ""
    }

    # 更宽松地匹配标题
    header = soup.find(string=re.compile(r"SABAH88.*LOTTO", re.IGNORECASE))
    if not header:
        print("⚠️ 未找到 'SABAH88 LOTTO' 标题")
        return None

    table = header.find_parent("table")
    if not table:
        print("⚠️ 未找到 SABAH88 LOTTO 数据表格")
        return None

    header_text = header.get_text(" ", strip=True)
    print(f"📅 标题文本: {header_text}")

    # 日期
    date_match = re.search(r"(\d{2}/\d{2}/\d{4})", header_text)
    if date_match:
        try:
            d = datetime.strptime(date_match.group(1), "%d/%m/%Y")
            data["draw_date"] = d.strftime("%d-%m-%Y")
            print(f"  提取到日期: {data['draw_date']}")
        except:
            pass

    # 期号
    no_match = re.search(r"(\d+/\d+)", header_text)
    if no_match:
        data["draw_no"] = no_match.group(1)
        print(f"  提取到期号: {data['draw_no']}")

    rows = table.find_all("tr")
    for row in rows:
        row_text = row.get_text()
        cells = row.find_all("td")

        # 开奖号码行
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

        # Jackpot 1
        if "Jackpot 1" in row_text:
            for cell in cells:
                text = cell.get_text(strip=True)
                amount_match = re.search(r'([\d,]+(?:\.\d+)?)', text)
                if amount_match:
                    data["jackpot1"] = amount_match.group(1)
                    print(f"  Jackpot 1: {data['jackpot1']}")
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
                            print(f"  Jackpot 1 (下一行): {data['jackpot1']}")
                            break

        # Jackpot 2
        if "Jackpot 2" in row_text:
            for cell in cells:
                text = cell.get_text(strip=True)
                amount_match = re.search(r'([\d,]+(?:\.\d+)?)', text)
                if amount_match:
                    data["jackpot2"] = amount_match.group(1)
                    print(f"  Jackpot 2: {data['jackpot2']}")
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
                            print(f"  Jackpot 2 (下一行): {data['jackpot2']}")
                            break

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

    # 2. 从 4dlatest.org 抓取 GDLOTTO 和 SABAH LOTTO
    print("\n🌕 正在从 4dlatest.org 抓取补充数据...")
    time.sleep(1)
    html_4dlatest = fetch_html(URL_4DLATEST)
    if html_4dlatest:
        soup_4dlatest = BeautifulSoup(html_4dlatest, "html.parser")
        
        # 2.1 抓取 GDLOTTO 豪龙
        gd_data = extract_gd_lotto_from_4dlatest(soup_4dlatest)
        if gd_data and gd_data.get('1st'):
            save_json('grand_dragon', gd_data)
        else:
            print("⚠️ GDLOTTO 豪龙数据为空，保留原有数据")
        
        # 2.2 抓取 SABAH88 沙巴万字 LOTTO
        sabah_data = extract_sabah_lotto_from_4dlatest(soup_4dlatest)
        if sabah_data and sabah_data.get('winning_numbers'):
            save_json('sabah_lotto', sabah_data)
        else:
            print("⚠️ SABAH88 沙巴万字 LOTTO 数据为空")
            
    else:
        print("❌ 无法获取 4dlatest.org 页面")

    update_dates_index()

if __name__ == "__main__":
    main()
