import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import re

URL = "https://4d4d.co/"

# 定义需要提取的最终公司及其对应的解析函数
# 每个键值对表示一个输出文件，值是一个元组：(outerbox索引, 提取函数, 公司显示名)
# 提取函数将接收 outerbox 的 soup 和全局日期，返回该公司的数据字典

def extract_damacai(box, global_date, global_draw_no):
    data = base_extract(box, global_date, global_draw_no)
    return data

def extract_magnum(box, global_date, global_draw_no):
    data = base_extract(box, global_date, global_draw_no)
    return data

def extract_toto(box, global_date, global_draw_no):
    data = base_extract(box, global_date, global_draw_no)
    return data

def extract_singapore(box, global_date, global_draw_no):
    data = base_extract(box, global_date, global_draw_no)
    return data

def extract_damacai_1p3d(box, global_date, global_draw_no):
    data = base_extract(box, global_date, global_draw_no)
    # 需要处理龙虎、奖金等额外字段？可后续扩展
    return data

def extract_sandakan(box, global_date, global_draw_no):
    data = base_extract(box, global_date, global_draw_no)
    return data

def extract_cashsweep(box, global_date, global_draw_no):
    data = base_extract(box, global_date, global_draw_no)
    return data

def extract_sabah(box, global_date, global_draw_no):
    data = base_extract(box, global_date, global_draw_no)
    # 提取 3D 结果
    data['3d'] = extract_3d(box)
    return data

def extract_sportstoto_5d(box, global_date, global_draw_no):
    data = base_extract(box, global_date, global_draw_no)
    data['type'] = '5d_table'
    # 提取 5D 表格
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

    # 提取自己的日期和期号
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

    # 如果没有自己的日期，使用全局
    if not data["draw_date"] and global_date:
        data["draw_date"] = global_date
    if not data["draw_no"] and global_draw_no:
        data["draw_no"] = global_draw_no

    # 前三名
    prize_tds = box.find_all("td", class_="resulttop")
    if len(prize_tds) >= 3:
        data["1st"] = prize_tds[0].get_text(strip=True)
        data["2nd"] = prize_tds[1].get_text(strip=True)
        data["3rd"] = prize_tds[2].get_text(strip=True)

    # 特别奖
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

    # 安慰奖
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

def extract_3d(box):
    """从 Sabah 的 outerbox 中提取 3D 结果"""
    # 找到 "3D" 标题后的表格
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
    """提取 5D 表格"""
    # 找到 "5D" 标题后的表格
    h5 = box.find("td", string=re.compile("5D"))
    if not h5:
        return []
    table = h5.find_parent("table")
    if not table:
        return []
    rows = table.find_all("tr")
    data = []
    for row in rows[1:]:  # 跳过标题
        tds = row.find_all("td")
        if len(tds) >= 2:
            # 格式可能是 [label, number] 或 [label, number, label, number]
            # 我们简单取前两个
            data.append([tds[0].get_text(strip=True), tds[1].get_text(strip=True)])
    return data

def extract_6d_table(box):
    """提取 6D 表格"""
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
    """提取 Star/Power/Supreme 乐透号码和奖池"""
    star = []
    power = []
    supreme = []
    jackpots = []

    # 查找 Star Toto 6/50
    star_section = box.find("td", string=re.compile("Star Toto 6/50"))
    if star_section:
        table = star_section.find_parent("table")
        if table:
            # 获取号码行
            num_row = table.find_all("tr")[1]  # 第二行
            tds = num_row.find_all("td", class_="resultbottomtoto2")
            star = [td.get_text(strip=True) for td in tds if td.get_text(strip=True) not in ['+', '']]
            # 奖池
            jp_rows = table.find_all("tr")[2:]  # 第三行开始
            for jp in jp_rows:
                jp_tds = jp.find_all("td", class_="resultbottomtotojpval")
                if jp_tds:
                    jackpots.append(jp_tds[0].get_text(strip=True))

    # 类似提取 Power 和 Supreme
    power_section = box.find("td", string=re.compile("Power Toto 6/55"))
    if power_section:
        table = power_section.find_parent("table")
        if table:
            num_row = table.find_all("tr")[1]
            tds = num_row.find_all("td", class_="resultbottomtoto2")
            power = [td.get_text(strip=True) for td in tds]

    supreme_section = box.find("td", string=re.compile("Supreme Toto 6/58"))
    if supreme_section:
        table = supreme_section.find_parent("table")
        if table:
            num_row = table.find_all("tr")[1]
            tds = num_row.find_all("td", class_="resultbottomtoto2")
            supreme = [td.get_text(strip=True) for td in tds]

    return star, power, supreme, jackpots

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

def main():
    html = fetch_html()
    if not html:
        return
    soup = BeautifulSoup(html, "html.parser")

    global_date, global_draw_no = extract_global_date(soup)
    print(f"🌍 全局日期: {global_date}, 全局期号: {global_draw_no}")

    outer_boxes = soup.find_all("div", class_="outerbox")
    print(f"📦 找到 {len(outer_boxes)} 个 outerbox")

    # 定义每个 outerbox 对应的公司列表（按顺序）
    # 根据页面内容，顺序应为：0:Damacai, 1:Magnum, 2:Toto, 3:SportsToto (复合), 4:DaMaCai1+3D, 5:Singapore, 6:Sabah, 7:Sandakan, 8:Cashsweep
    # 我们需要为每个 outerbox 调用相应的提取函数
    box_handlers = [
        [('damacai', extract_damacai)],
        [('magnum', extract_magnum)],
        [('toto', extract_toto)],
        [   # SportsToto 复合 box
            ('sportstoto_5d', extract_sportstoto_5d),
            ('sportstoto_6d', extract_sportstoto_6d),
            ('sportstoto_lotto', extract_sportstoto_lotto),
        ],
        [('damacai_1p3d', extract_damacai_1p3d)],
        [('singapore', extract_singapore)],
        [('sabah', extract_sabah)],
        [('sandakan', extract_sandakan)],
        [('sarawak_cashsweep', extract_cashsweep)],
    ]

    if len(outer_boxes) != len(box_handlers):
        print(f"⚠️ outerbox 数量 ({len(outer_boxes)}) 与预期 ({len(box_handlers)}) 不符，请检查页面结构")

    for idx, box in enumerate(outer_boxes):
        if idx >= len(box_handlers):
            print(f"⚠️ 超出预期的 outerbox 索引 {idx}，跳过")
            continue
        handlers = box_handlers[idx]
        for company_key, extract_func in handlers:
            print(f"🔍 正在处理 {company_key}...")
            data = extract_func(box, global_date, global_draw_no)
            save_json(company_key, data)

    update_dates_index()

if __name__ == "__main__":
    main()
