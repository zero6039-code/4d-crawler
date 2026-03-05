import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import re

URL = "https://4d4d.co/"

# ---------- 通用智能提取函数 ----------
def smart_extract(box, global_date, global_draw_no):
    """
    智能解析 4D 盒子，通过单元格位置识别奖项，兼容西马、东马和新加坡
    """
    data = {
        "draw_date": global_date,
        "draw_no": global_draw_no,
        "1st": "----", "2nd": "----", "3rd": "----",
        "special": [], "consolation": []
    }

    # 1. 尝试从盒子里找期号（如果盒子内有自己的期号则覆盖全局）
    draw_no_tag = box.find(text=re.compile(r'\d{4,}/\d{2}'))
    if draw_no_tag:
        data["draw_no"] = draw_no_tag.strip()

    # 2. 提取所有包含 4 位数字的单元格
    all_tds = box.find_all("td")
    four_digit_numbers = []
    for td in all_tds:
        txt = td.get_text(strip=True)
        if len(txt) == 4 and txt.isdigit():
            four_digit_numbers.append(txt)

    if not four_digit_numbers:
        return data

    # 3. 按位置分配奖项 (通用的 4D 结构)
    # 前 3 个是头、二、三奖
    if len(four_digit_numbers) >= 1: data["1st"] = four_digit_numbers[0]
    if len(four_digit_numbers) >= 2: data["2nd"] = four_digit_numbers[1]
    if len(four_digit_numbers) >= 3: data["3rd"] = four_digit_numbers[2]

    # 剩余的是特别奖和安慰奖
    remaining = four_digit_numbers[3:]
    if len(remaining) > 0:
        # 典型的 4D 游戏有 10 个特别奖，10 个安慰奖
        # 如果剩下 20 个，前 10 是 Special，后 10 是 Consolation
        if len(remaining) == 20:
            data["special"] = remaining[:10]
            data["consolation"] = remaining[10:]
        elif len(remaining) == 13: # 有些公司是 13 个特别奖
            data["special"] = remaining
        else:
            data["special"] = remaining

    return data

# ---------- 存储函数 ----------
def save_json(company_name, data):
    if not data: return
    
    # 存入当日文件夹
    date_str = data.get("draw_date", "unknown")
    folder = f"data/{date_str}"
    os.makedirs(folder, exist_ok=True)
    with open(f"{folder}/{company_name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    # 同时存一份最新的到根目录供页面默认加载
    with open(f"data/{company_name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"✅ 已保存: {company_name}")

# ---------- 主爬虫逻辑 ----------
def main():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(URL, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, "html.parser")

        # 提取全局日期
        date_tag = soup.find("td", class_="drawdate")
        global_date = datetime.now().strftime("%d-%m-%Y")
        if date_tag:
            raw_date = date_tag.get_text(strip=True)
            match = re.search(r'(\d{2}-\d{2}-\d{4})', raw_date)
            if match: global_date = match.group(1)

        # 提取全局期号
        draw_no_tag = soup.find("td", class_="drawno")
        global_draw_no = draw_no_tag.get_text(strip=True) if draw_no_tag else ""

        outer_boxes = soup.find_all("div", class_="outerbox")
        print(f"📦 发现 {len(outer_boxes)} 个数据区块，开始解析...")

        for idx, box in enumerate(outer_boxes):
            box_text = box.get_text(" ", strip=True).upper()
            
            # --- 智能匹配公司关键词 ---
            if "MAGNUM" in box_text:
                save_json('magnum', smart_extract(box, global_date, global_draw_no))
            elif "DAMACAI" in box_text and "1+3D" in box_text:
                save_json('damacai', smart_extract(box, global_date, global_draw_no))
            elif "TOTO" in box_text and "4D" in box_text and "SPORTSTOTO" not in box_text:
                save_json('toto', smart_extract(box, global_date, global_draw_no))
            elif "SINGAPORE" in box_text:
                save_json('singapore', smart_extract(box, global_date, global_draw_no))
            elif "SABAH" in box_text:
                save_json('sabah', smart_extract(box, global_date, global_draw_no))
            elif "SANDAKAN" in box_text:
                save_json('sandakan', smart_extract(box, global_date, global_draw_no))
            elif "SWEEP" in box_text or "CASH SWEEP" in box_text:
                save_json('sarawak_cashsweep', smart_extract(box, global_date, global_draw_no))
            elif "GRAND DRAGON" in box_text or "GDBL" in box_text:
                save_json('grand_dragon', smart_extract(box, global_date, global_draw_no))
            
            # 特殊处理 SportsToto 复合盒 (5D/6D/Lotto)
            elif "SPORTSTOTO" in box_text:
                # 这里可以保留你原本针对 5D/6D 的 extract_sportstoto 函数逻辑
                pass

        # 更新日期索引
        update_dates_index(global_date)

    except Exception as e:
        print(f"❌ 运行出错: {e}")

def update_dates_index(new_date):
    index_path = "data/dates.json"
    dates = []
    if os.path.exists(index_path):
        with open(index_path, "r") as f: dates = json.load(f)
    if new_date not in dates:
        dates.append(new_date)
        with open(index_path, "w") as f: json.dump(dates, f)

if __name__ == "__main__":
    main()
