import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import re

# ---------- 配置 ----------
URL_4D4D = "https://4d4d.co/"
URL_4DMOON_SG = "https://www.4dmoon.com/singapore-4d-results/"

# ---------- 基础辅助函数 ----------
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

def parse_4dmoon_date(date_str):
    """将 02-Mar-2026 转换为 02-03-2026"""
    try:
        d = datetime.strptime(date_str.strip(), "%d-%b-%Y")
        return d.strftime("%d-%m-%Y")
    except:
        return None

# ---------- 4d4d.co 专用提取逻辑 ----------
def extract_global_date(soup):
    """从页面顶部提取全局日期和期号"""
    first_box = soup.find("div", class_="outerbox")
    if not first_box: return None, None
    draw_row = first_box.find("td", class_="resultdrawdate")
    if not draw_row: return None, None
    
    date_text = draw_row.get_text(strip=True)
    match = re.search(r"(\d{2}-\d{2}-\d{4})", date_text)
    date = match.group(1) if match else None
    
    next_td = draw_row.find_next("td", class_="resultdrawdate")
    draw_no = None
    if next_td:
        no_text = next_td.get_text(strip=True)
        draw_no = re.sub(r"Draw No:?", "", no_text).strip()
    return date, draw_no

def base_extract(box, global_date, global_draw_no):
    """通用 4D 格式提取器"""
    data = {
        "draw_date": global_date or "",
        "draw_no": global_draw_no or "",
        "1st": "", "2nd": "", "3rd": "",
        "special": [], "consolation": [], "type": None
    }
    # 尝试从 box 内部提取更准确的日期/期号
    draw_row = box.find("td", class_="resultdrawdate")
    if draw_row:
        dt_match = re.search(r"(\d{2}-\d{2}-\d{4})", draw_row.get_text(strip=True))
        if dt_match: data["draw_date"] = dt_match.group(1)
        next_td = draw_row.find_next("td", class_="resultdrawdate")
        if next_td: data["draw_no"] = re.sub(r"Draw No:?", "", next_td.get_text(strip=True)).strip()

    prize_tds = box.find_all("td", class_="resulttop")
    if len(prize_tds) >= 3:
        data["1st"] = prize_tds[0].get_text(strip=True)
        data["2nd"] = prize_tds[1].get_text(strip=True)
        data["3rd"] = prize_tds[2].get_text(strip=True)

    # 提取特别奖和安慰奖
    for key, pattern in [("special", "Special|特別獎"), ("consolation", "Consolation|安慰獎")]:
        section = box.find("td", string=re.compile(pattern))
        if section:
            table = section.find_parent("table")
            if table:
                data[key] = [td.get_text(strip=True) for td in table.find_all("td", class_="resultbottom") 
                             if td.get_text(strip=True) and td.get_text(strip=True) != "----"]
    return data

# (此处省略部分您已提供的特殊 4D 提取子函数，如 extract_5d_table, extract_lotto 等，保持原样即可)
# ... [保留您代码中的 extract_3d, extract_5d_table, extract_6d_table, extract_lotto, extract_singapore 等] ...

# ========== 整合后的 Singapore Toto (4dmoon) 提取函数 ==========
def extract_singapore_toto_4dmoon(soup):
    print("🔍 开始解析 4dmoon 的 Singapore Toto 数据...")
    data = {"draw_date": "", "draw_no": "", "winning_numbers": [], "prize_table": []}

    toto_header = soup.find("td", string=re.compile(r"Singapore\s*Toto", re.I))
    if not toto_header:
        for td in soup.find_all("td"):
            if "Singapore" in td.text and "Toto" in td.text:
                toto_header = td; break
    
    if not toto_header: return None

    full_text = toto_header.find_parent("td").get_text(" ", strip=True) if toto_header.find_parent("td") else toto_header.get_text(" ", strip=True)
    
    date_match = re.search(r"(\d{2}-[A-Za-z]{3}-\d{4})", full_text)
    if date_match:
        data["draw_date"] = parse_4dmoon_date(date_match.group(1))
    
    no_match = re.search(r"#(\d+)", full_text)
    if no_match: data["draw_no"] = no_match.group(1)

    table = toto_header.find_parent("table")
    if table:
        for row in table.find_all("tr"):
            row_text = row.get_text()
            if sum(c.isdigit() for c in row_text) > 5 and "+" in row_text:
                data["winning_numbers"] = [td.get_text(strip=True) for td in row.find_all("td") if td.get_text(strip=True).isdigit()]
                break

    prize_header = soup.find("td", string=re.compile(r"Prize Group|Share Amount", re.I))
    if prize_header:
        p_table = prize_header.find_parent("table")
        if p_table:
            for row in p_table.find_all("tr")[1:]:
                cells = row.find_all("td")
                if len(cells) >= 3:
                    data["prize_table"].append([c.get_text(strip=True) for c in cells[:3]])
    return data

# ---------- 存储逻辑 ----------
def save_json(company, data):
    if not data or not data.get("draw_date"):
        print(f"⚠️ {company} 数据不完整，跳过保存")
        return
    
    base_dir = "docs/data"
    os.makedirs(base_dir, exist_ok=True)

    # 保存最新文件
    with open(os.path.join(base_dir, f"{company}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 归档历史文件
    try:
        folder_date = datetime.strptime(data["draw_date"], "%d-%m-%Y").strftime("%Y-%m-%d")
    except:
        folder_date = datetime.now().strftime("%Y-%m-%d")
    
    archive_dir = os.path.join(base_dir, folder_date)
    os.makedirs(archive_dir, exist_ok=True)
    with open(os.path.join(archive_dir, f"{company}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ {company} 已更新并归档 ({folder_date})")

def update_dates_index():
    base_dir = "docs/data"
    dates = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and re.match(r"\d{4}-\d{2}-\d{2}", d)]
    dates.sort(reverse=True)
    with open(os.path.join(base_dir, "dates.json"), "w", encoding="utf-8") as f:
        json.dump(dates, f)
    print(f"📋 索引更新完成，共 {len(dates)} 天记录")

# ---------- 主程序 ----------
def main():
    print("🚀 爬虫任务开始")
    
    # 1. 处理 4D4D.co 数据
    html_4d = fetch_html(URL_4D4D)
    processed_count = 0
    if html_4d:
        soup = BeautifulSoup(html_4d, "html.parser")
        g_date, g_no = extract_global_date(soup)
        
        # 定义匹配器
        matchers = [
            (re.compile(r'GRAND\s+DRAGON', re.I), 'grand_dragon', lambda b, d, n: base_extract(b, d, n)),
            (re.compile(r'DAMACAI.*4D', re.I), 'damacai', lambda b, d, n: base_extract(b, d, n)),
            (re.compile(r'MAGNUM.*4D', re.I), 'magnum', lambda b, d, n: base_extract(b, d, n)),
            (re.compile(r'TOTO.*4D', re.I), 'toto', lambda b, d, n: base_extract(b, d, n)),
            (re.compile(r'SINGAPORE.*4D', re.I), 'singapore', extract_singapore), # 使用您的 SG 专用函数
            (re.compile(r'DA MA CAI 1\+3D', re.I), 'damacai_1p3d', lambda b, d, n: base_extract(b, d, n)),
            (re.compile(r'SABAH.*88', re.I), 'sabah', extract_sabah),
            (re.compile(r'SANDAKAN', re.I), 'sandakan', lambda b, d, n: base_extract(b, d, n)),
            (re.compile(r'CASHWEEP', re.I), 'sarawak_cashsweep', lambda b, d, n: base_extract(b, d, n))
        ]

        for idx, box in enumerate(soup.find_all("div", class_="outerbox")):
            box_text = box.get_text(" ", strip=True).upper()
            for pattern, key, func in matchers:
                if pattern.search(box_text):
                    data = func(box, g_date, g_no)
                    save_json(key, data)
                    processed_count += 1
            
            # 特殊处理 SportsToto 复合框
            if "SPORTSTOTO" in box_text:
                for sub_key, sub_func in [('sportstoto_5d', extract_sportstoto_5d), 
                                         ('sportstoto_6d', extract_sportstoto_6d), 
                                         ('sportstoto_lotto', extract_sportstoto_lotto)]:
                    data = sub_func(box, g_date, g_no)
                    if data.get('data') or data.get('star'): # 简单检查有效性
                        save_json(sub_key, data)
                        processed_count += 1

    # 2. 处理 4DMOON (Singapore Toto)
    html_moon = fetch_html(URL_4DMOON_SG)
    if html_moon:
        moon_soup = BeautifulSoup(html_moon, "html.parser")
        toto_data = extract_singapore_toto_4dmoon(moon_soup)
        if toto_data:
            save_json('singapore_toto', toto_data)
            processed_count += 1

    # 3. 更新索引
    update_dates_index()
    print(f"🏁 任务完成，本次更新 {processed_count} 个公司数据")

if __name__ == "__main__":
    main()
