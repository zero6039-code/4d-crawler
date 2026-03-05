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
    """将 02-Mar-2026 转换为 02-03-2026 (保留此函数，可能用于新网站的日期格式)"""
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
# ... (extract_damacai, extract_magnum, extract_toto, extract_singapore, extract_damacai_1p3d, extract_sandakan, extract_cashsweep, extract_sabah, extract_sportstoto_5d, extract_sportstoto_6d, extract_sportstoto_lotto, extract_grand_dragon, base_extract, extract_3d, extract_5d_table, extract_6d_table, extract_lotto) ...
# 为了节省篇幅，这里省略了您原有从 4d4d.co 抓取的所有函数，请将它们完整保留。

# ========== 从 4dlatest.org 提取 GDLOTTO 豪龙数据 ==========
def extract_gd_lotto_from_4dlatest(soup):
    """
    从 https://4dlatest.org/ 的 HTML 中提取 "GDLOTTO 豪龙" 的数据。
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

    # 定位到 "GDLOTTO 豪龙" 部分
    # 页面中该部分标题为 "GDLOTTO 豪龙"，它通常在一个 <h2> 或类似标签中
    header = soup.find(lambda tag: tag.name in ['h2', 'h3', 'strong'] and "GDLOTTO 豪龙" in tag.get_text())
    if not header:
        print("⚠️ 未找到 'GDLOTTO 豪龙' 标题")
        return None
    print(f"✅ 找到标题: {header.get_text(strip=True)}")

    # 向上找到包含整个公司的容器，通常是一个 <div> 或父级标签
    # 这里我们假设标题之后紧跟的是数据表格所在的容器，通过查找下一个 <table> 或兄弟元素
    # 一个简单的方法是：找到标题后，遍历其后续兄弟节点，直到找到包含数据的表格
    container = header.find_next()
    # 或者更简单：假设数据在标题所在的父级区域内
    parent_section = header.find_parent('div')  # 假设数据在同一个 div 内

    # 提取日期和期号（通常在标题行中）
    # 例如标题可能是 "GDLOTTO 豪龙 05/03/2026 (Thu)"
    header_text = header.get_text()
    # 匹配日期格式 DD/MM/YYYY
    date_match = re.search(r'(\d{2}/\d{2}/\d{4})', header_text)
    if date_match:
        try:
            d = datetime.strptime(date_match.group(1), "%d/%m/%Y")
            data["draw_date"] = d.strftime("%d-%m-%Y")
            print(f"  提取到日期: {data['draw_date']}")
        except:
            pass

    # 提取前三名、特别奖、安慰奖
    # 我们需要找到包含这些数据的表格或列表。
    # 从页面结构看，数据可能以表格或特定 class 的 div 呈现。
    # 这里我们采用一个更通用的方法：查找当前部分内所有包含数字的段落。

    # 如果找到了父容器，就在其中查找
    target_section = parent_section if parent_section else header.parent
    if target_section:
        # 提取特别奖和安慰奖通常需要找到对应的文本标签
        # 示例：查找包含 "SPECIAL" 和 "CONSOLATION" 的区域
        special_tag = target_section.find(string=re.compile(r'SPECIAL', re.I))
        consolation_tag = target_section.find(string=re.compile(r'CONSOLATION', re.I))

        # 提取前三名
        prize_rows = target_section.find_all('tr')  # 假设数据在表格行中
        if prize_rows:
            for row in prize_rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).upper()
                    number = cells[1].get_text(strip=True)
                    if '1ST' in label:
                        data['1st'] = number
                    elif '2ND' in label:
                        data['2nd'] = number
                    elif '3RD' in label:
                        data['3rd'] = number

        # 提取特别奖和安慰奖的数字（需要根据实际页面结构调整）
        # 这里只是一个示例，您需要根据 4dlatest.org 的实际 HTML 结构来编写精确的提取逻辑
        # 例如，特别奖的数字可能位于一个 <div class="special"> 内
        special_numbers = []
        if special_tag:
            # 找到包含数字的父元素或后续元素
            special_container = special_tag.find_parent()
            if special_container:
                # 假设数字在一系列 <td> 或 <span> 中
                number_elements = special_container.find_all('td')
                for elem in number_elements:
                    num = elem.get_text(strip=True)
                    if num.isdigit() and num != '----':
                        special_numbers.append(num)
        data['special'] = special_numbers

        consolation_numbers = []
        if consolation_tag:
            consolation_container = consolation_tag.find_parent()
            if consolation_container:
                number_elements = consolation_container.find_all('td')
                for elem in number_elements:
                    num = elem.get_text(strip=True)
                    if num.isdigit() and num != '----':
                        consolation_numbers.append(num)
        data['consolation'] = consolation_numbers

        # 提取 Jackpot
        jackpot_tag = target_section.find(string=re.compile(r'Jackpot', re.I))
        if jackpot_tag:
            # 假设金额在同一个元素或下一个兄弟元素中
            amount_elem = jackpot_tag.find_next()
            if amount_elem:
                data['jackpot'] = amount_elem.get_text(strip=True)
            else:
                # 尝试从包含 Jackpot 的整行文本中提取
                jackpot_text = jackpot_tag.parent.get_text()
                amount_match = re.search(r'Jackpot\s*\|\s*([\d,\.]+)', jackpot_text)
                if amount_match:
                    data['jackpot'] = amount_match.group(1)

    else:
        print("⚠️ 未能定位 GDLOTTO 豪龙的数据容器")

    return data

# ---------- 保存 JSON 和索引更新 ----------
def save_json(company, data):
    # ... (此函数保持不变) ...
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
    # 1. 抓取 4d4d.co 数据 (包含 damacai, magnum, toto 等，但不再包含 Singapore 4D 和 Grand Dragon)
    html_4d4d = fetch_html(URL_4D4D)
    if html_4d4d:
        soup_4d4d = BeautifulSoup(html_4d4d, "html.parser")
        global_date, global_draw_no = extract_global_date(soup_4d4d)
        print(f"🌍 4d4d.co 全局日期: {global_date}, 全局期号: {global_draw_no}")
        outer_boxes = soup_4d4d.find_all("div", class_="outerbox")
        print(f"📦 找到 {len(outer_boxes)} 个 outerbox")

        # 注意：这里移除了 Singapore 4D 的匹配项，因为我们计划从新网站获取
        company_matchers = [
            (re.compile(r'GRAND\s+DRAGON', re.I), 'grand_dragon', extract_grand_dragon), # 保留，但数据可能从新网站覆盖
            (re.compile(r'DAMACAI.*4D', re.I), 'damacai', extract_damacai),
            (re.compile(r'MAGNUM.*4D', re.I), 'magnum', extract_magnum),
            (re.compile(r'TOTO.*4D', re.I), 'toto', extract_toto),
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

    # 2. 从 4dlatest.org 抓取 GDLOTTO 豪龙数据
    print("\n🌕 正在从 4dlatest.org 抓取 GDLOTTO 豪龙数据...")
    time.sleep(1)  # 礼貌延时
    html_4dlatest = fetch_html(URL_4DLATEST)
    if html_4dlatest:
        soup_4dlatest = BeautifulSoup(html_4dlatest, "html.parser")
        gd_data = extract_gd_lotto_from_4dlatest(soup_4dlatest)
        if gd_data:
            save_json('grand_dragon', gd_data)  # 注意：公司 key 仍为 'grand_dragon'，但数据来自新网站
        else:
            print("⚠️ GDLOTTO 豪龙数据为空")
    else:
        print("❌ 无法获取 4dlatest.org 页面")

    update_dates_index()

if __name__ == "__main__":
    main()
