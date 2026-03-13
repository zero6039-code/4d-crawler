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

# ---------- 4d4d.co 相关提取函数（保持不变）----------
# ... 为节省篇幅，此处省略原有所有提取函数，实际使用时请保留 ...

# ================== 从 dato4d.com JSON 抓取 Grand Dragon 数据（新源）==================
def fetch_grand_dragon_from_dato4d_json():
    """从 https://www.dato4d.com/liveos.json 获取 Grand Dragon 4D 数据（结构化JSON）"""
    print("🔍 正在从 dato4d.com JSON 获取 Grand Dragon 4D 数据...")
    # 添加时间戳防止缓存
    url = "https://www.dato4d.com/liveos.json?_=" + str(int(time.time()*1000))
    html = fetch_html(url)
    if not html:
        return None

    try:
        data = json.loads(html)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        return None

    # 检查是否存在 Grand Dragon 数据 (键 "G")
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
        "jackpot": ""  # JSON 中无 Jackpot 信息
    }

    # 提取日期 (格式如 "13-03-2026 (Fri)")
    raw_date = g.get("DD", "")
    date_match = re.search(r"(\d{2}-\d{2}-\d{4})", raw_date)
    if date_match:
        result["draw_date"] = date_match.group(1)
        print(f"  ✅ 提取到日期: {result['draw_date']}")

    # 提取 Special Prize (S1 到 S13，排除 "----")
    for i in range(1, 14):
        key = f"S{i}"
        if key in g:
            num = g[key]
            if num and num != "----":
                result["special"].append(num)
    print(f"  ✅ 特别奖数量: {len(result['special'])}")

    # 提取 Consolation Prize (C1 到 C10，排除 "----")
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

# ================== 原有从 gdlotto.net 抓取 Grand Dragon 函数（保留作为备胎）==================
def fetch_grand_dragon_from_gdlotto_net():
    # ... 原有代码保持不变 ...
    pass

# ================== 原有其他补充源函数（保持不变）==================
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

def extract_sportstoto_from_4dlatest(soup):
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

        # ... 原有处理4d4d.co公司的代码保持不变 ...
        # 为节省篇幅，此处省略，实际使用时保留

    # 2. 从 4dlatest.org 抓取补充数据
    print("\n🌕 正在从 4dlatest.org 抓取补充数据...")
    time.sleep(1)
    html_4dlatest = fetch_html(URL_4DLATEST)
    if html_4dlatest:
        soup_4dlatest = BeautifulSoup(html_4dlatest, "html.parser")

        # ★★★ 2.1 GDLOTTO 豪龙 - 优先使用 dato4d.com JSON ★★★
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

if __name__ == "__main__":
    main()
