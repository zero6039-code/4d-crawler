import os
import re
import time
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from crawler_http import *
from crawler_parsers_html import *
from crawler_parsers_json import *
from crawler_backup_sources import *
from crawler_storage import *

# ---------- 主流程 ----------
def main():
    print("🚀 爬虫开始运行")

    is_manual = os.getenv('IS_MANUAL') == 'true'

    if not is_manual:
        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz)
        
        target_start = now.replace(hour=19, minute=0, second=0, microsecond=0)
        target_end = now.replace(hour=22, minute=30, second=0, microsecond=0)
        
        if now < target_start or now >= target_end:
            print("当前不在抓取时段（19:00–22:30），退出。")
            return
    else:
        print("手动触发模式，跳过时段检查。")

    if not is_manual:
        max_attempts = 6
        attempt = 0
        json_success = False
        while attempt < max_attempts and not json_success:
            print(f"第 {attempt+1} 次尝试抓取 JSON 数据...")
            json_success = fetch_all_companies_from_dato4d(require_fresh=True)
            if json_success:
                print("JSON 抓取成功，且三大公司均为当天开奖数据！")
                break
            else:
                print("当天开奖数据未就绪或抓取失败，3分钟后重试...")
                time.sleep(180)
                attempt += 1
        else:
            print("时段内多次尝试均未拿到当天开奖数据。")
    else:
        json_success = fetch_all_companies_from_dato4d(require_fresh=True)

    # ========== 主源失败/不新鲜时才用备用源；手动模式保持原行为 ==========
    if not json_success or is_manual:
        print("🔄 正在从备用源获取 Perdana 和 Lucky HariHari 的晚间场数据...")
        backup_data = fetch_backup_sources()
        for key, data in backup_data.items():
            if data and (any(data.get(k) for k in ['1st', '2nd', '3rd']) or data.get('winning_numbers')):
                save_json(key, data)
                print(f"✅ 已使用备用源更新 {key}")
            
    # 如果 JSON 源失败，则回退到 4d4d.co 抓取
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

    # 更新日期索引 + 生成前端聚合文件
    update_dates_index()
    try:
        build_latest()
    except Exception as e:
        print(f"⚠️ 生成聚合文件失败: {e}")
    if json_success or LAST_SAVED_COUNT:
        update_sitemap()
    print("🔚 爬虫执行完毕")

if __name__ == "__main__":
    main()
