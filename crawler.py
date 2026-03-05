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
    if not date_str:
        return None
    date_str = date_str.strip()
    patterns = [
        r"(\d{2}-[A-Za-z]{3}-\d{4})",
        r"(\d{2}\s+[A-Za-z]{3}\s+\d{4})",
        r"(\d{4}-\d{2}-\d{2})"
    ]
    for pattern in patterns:
        match = re.search(pattern, date_str)
        if match:
            try:
                d = datetime.strptime(match.group(1), "%d-%b-%Y")
                return d.strftime("%d-%m-%Y")
            except:
                try:
                    d = datetime.strptime(match.group(1), "%d %b %Y")
                    return d.strftime("%d-%m-%Y")
                except:
                    try:
                        d = datetime.strptime(match.group(1), "%Y-%m-%d")
                        return d.strftime("%d-%m-%Y")
                    except:
                        pass
    return None

# ---------- 4d4d.co 提取函数（与您原有代码相同，此处省略以节省篇幅，实际使用时请保留）----------
# ... 您的全部 4d4d.co 提取函数（extract_damacai, base_extract, main_4d4d 等）...

# ---------- 4dmoon.com 提取函数（需完整添加）----------
def find_section(soup, patterns):
    for pattern in patterns:
        elem = soup.find("td", string=re.compile(pattern, re.I))
        if elem:
            return elem, pattern
    return None, None

def extract_grand_dragon_4dmoon(soup):
    patterns = [r"Grand\s*Dragon\s*4D", r"GRAND\s*DRAGON"]
    section, used_pattern = find_section(soup, patterns)
    if not section:
        return None
    print(f"✅ 找到 Grand Dragon (匹配: {used_pattern})")
    parent = section.find_parent("td")
    parent_text = parent.get_text(" ", strip=True) if parent else ""
    draw_date = parse_4dmoon_date(parent_text)
    data = {"draw_date": draw_date or "", "draw_no": "", "1st": "", "2nd": "", "3rd": "", "special": [], "consolation": []}
    table = find_parent_table(section)
    if not table:
        return data
    prize_cells = table.find_all("td", class_=re.compile(r"resulttop|prize", re.I))
    if len(prize_cells) >= 3:
        data["1st"] = prize_cells[0].get_text(strip=True)
        data["2nd"] = prize_cells[1].get_text(strip=True)
        data["3rd"] = prize_cells[2].get_text(strip=True)
    special_header = table.find("td", string=re.compile(r"Special|特別獎", re.I))
    if special_header:
        row = special_header.find_parent("tr")
        if row:
            cells = row.find_all("td")[1:]
            data["special"] = [c.get_text(strip=True) for c in cells if c.get_text(strip=True) not in ["----", ""]]
    cons_header = table.find("td", string=re.compile(r"Consolation|安慰獎", re.I))
    if cons_header:
        row = cons_header.find_parent("tr")
        if row:
            cells = row.find_all("td")[1:]
            data["consolation"] = [c.get_text(strip=True) for c in cells if c.get_text(strip=True) not in ["----", ""]]
    return data

def extract_sportstoto_fireball_4dmoon(soup):
    patterns = [r"SportsToto\s*Fireball", r"FIREBALL"]
    section, used_pattern = find_section(soup, patterns)
    if not section:
        return None
    print(f"✅ 找到 Fireball (匹配: {used_pattern})")
    parent = section.find_parent("td")
    parent_text = parent.get_text(" ", strip=True) if parent else ""
    draw_date = parse_4dmoon_date(parent_text)
    no_match = re.search(r"#(\d+/\d+)", parent_text)
    draw_no = no_match.group(1) if no_match else ""
    data = {"draw_date": draw_date or "", "draw_no": draw_no, "data": []}
    table = find_parent_table(section)
    if table:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True)
                if "Fireball" not in label:
                    data["data"].append([label, cells[1].get_text(strip=True)])
    return data

def extract_singapore_toto_4dmoon(soup):
    patterns = [r"Singapore Toto", r"SINGAPORE TOTO"]
    section, used_pattern = find_section(soup, patterns)
    if not section:
        return None
    print(f"✅ 找到 Singapore Toto (匹配: {used_pattern})")
    parent = section.find_parent("td")
    parent_text = parent.get_text(" ", strip=True) if parent else ""
    draw_date = parse_4dmoon_date(parent_text)
    no_match = re.search(r"#(\d+)", parent_text)
    draw_no = no_match.group(1) if no_match else ""
    data = {"draw_date": draw_date or "", "draw_no": draw_no, "winning_numbers": [], "prize_table": []}
    table = find_parent_table(section)
    if table:
        rows = table.find_all("tr")
        if len(rows) >= 2:
            num_row = rows[1]
            tds = num_row.find_all("td")
            data["winning_numbers"] = [td.get_text(strip=True) for td in tds if td.get_text(strip=True) and td.get_text(strip=True) != '+']
    prize_section, _ = find_section(soup, [r"Prize Group", r"PRIZE GROUP"])
    if prize_section:
        prize_table = find_parent_table(prize_section)
        if prize_table:
            prize_rows = prize_table.find_all("tr")[1:]
            for row in prize_rows:
                cells = row.find_all("td")
                if len(cells) >= 3:
                    data["prize_table"].append([cells[0].get_text(strip=True), cells[1].get_text(strip=True), cells[2].get_text(strip=True)])
    return data

def extract_magnum_jackpot_gold_4dmoon(soup):
    patterns = [r"4D Jackpot Estimated Amount", r"MAGNUM JACKPOT"]
    section, used_pattern = find_section(soup, patterns)
    if not section:
        return None
    print(f"✅ 找到 Magnum Jackpot (匹配: {used_pattern})")
    parent = section.find_parent("td")
    parent_text = parent.get_text(" ", strip=True) if parent else ""
    draw_date = parse_4dmoon_date(parent_text)
    no_match = re.search(r"#(\d+/\d+)", parent_text)
    draw_no = no_match.group(1) if no_match else ""
    data = {"draw_date": draw_date or "", "draw_no": draw_no, "data": []}
    table = find_parent_table(section)
    if table:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 2:
                data["data"].append([cells[0].get_text(strip=True), cells[1].get_text(strip=True)])
    return data

# 为其他公司（sportstoto_5d/6d/lotto 在 4dmoon 上可能已有，但您已从 4d4d 抓取，可忽略）
# 但若您想从 4dmoon 补充，可类似添加函数。

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

# ---------- 主流程整合 ----------
def main():
    # 1. 抓取 4d4d.co
    html_4d4d = fetch_html(URL_4D4D)
    if html_4d4d:
        soup_4d4d = BeautifulSoup(html_4d4d, "html.parser")
        global_date, global_draw_no = extract_global_date(soup_4d4d)  # 您需要保留此函数
        print(f"🌍 4d4d.co 全局日期: {global_date}")
        outer_boxes = soup_4d4d.find_all("div", class_="outerbox")
        print(f"📦 找到 {len(outer_boxes)} 个 outerbox")
        # ... 此处插入您的公司匹配和提取逻辑（从您的原 main 函数复制）...
        # 为节省篇幅，请将您的原 main 函数中关于 4d4d 的处理逻辑放在这里
        # 您可以直接将之前的 main_4d4d 函数内容复制到这里

    # 2. 抓取 4dmoon.com
    print("\n🌙 正在从 4dmoon.com 抓取补充数据...")
    html_moon = fetch_html(URL_4DMOON)
    if html_moon:
        soup_moon = BeautifulSoup(html_moon, "html.parser")
        moon_extractors = [
            ('grand_dragon', extract_grand_dragon_4dmoon),
            ('sportstoto_fireball', extract_sportstoto_fireball_4dmoon),
            ('singapore_toto', extract_singapore_toto_4dmoon),
            ('magnum_jackpot_gold', extract_magnum_jackpot_gold_4dmoon),
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

    update_dates_index()

if __name__ == "__main__":
    main()
