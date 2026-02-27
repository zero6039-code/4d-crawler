import subprocess
import json
import os
from datetime import datetime
import re

# 公司映射
COMPANY_MAPPING = {
    "damacai": "DMC",      # Da Ma Cai
    "magnum": "MAG",        # Magnum
    "toto": "TOT",          # Sports Toto
    "singapore": "SGP",     # Singapore Pools
    "sandakan": "STC",      # Sandakan
    "sarawak_cashsweep": "CSP",  # Cash Sweep
    "sabah": "S88",         # Sabah 88
    # 注意：以下公司可能没有直接对应，需要从其他源获取
    "damacai_1p3d": "DMC",  # 同damacai，但需要额外处理
    "sabah_lotto": "S88",   # 同sabah
    "sportstoto_fireball": "TOT",  # Sports Toto 的子项
    "grand_dragon": "GDL",  # Grand Dragon Lotto
    "singapore_toto": "SGP",  # Singapore Toto
    "sportstoto_lotto": "TOT",
    "magnum_jackpot_gold": "MAG",
    "sportstoto_5d": "TOT",
    "sportstoto_6d": "TOT",
    "magnum_life": "MAG",
}

def fetch_from_mcp(pid):
    """调用 asean-lottery-mcp 获取数据"""
    try:
        result = subprocess.run(
            ['npx', '-y', 'asean-lottery-mcp', '--company', pid],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"❌ MCP 调用失败: {result.stderr}")
            return None
    except Exception as e:
        print(f"❌ MCP 异常: {e}")
        return None

def parse_mcp_data(pid, raw_data):
    """将MCP返回的数据转换为您的统一格式"""
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
    
    if raw_data:
        # MCP返回的数据格式可能需要根据实际情况调整
        data["draw_date"] = raw_data.get("draw_date", "")
        data["1st"] = raw_data.get("first_prize", "")
        data["2nd"] = raw_data.get("second_prize", "")
        data["3rd"] = raw_data.get("third_prize", "")
        data["special"] = raw_data.get("special", [])
        data["consolation"] = raw_data.get("consolation", [])
    
    return data

def save_json(company, data):
    """保存JSON文件（与之前相同）"""
    if not data:
        print(f"❌ {company} 数据为空，跳过保存")
        return
    base_dir = "docs/data"
    os.makedirs(base_dir, exist_ok=True)

    latest_path = os.path.join(base_dir, f"{company}.json")
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已更新最新文件: {latest_path}")

    # 归档逻辑保持不变
    draw_date = data.get("draw_date", "")
    if not draw_date or draw_date == "----":
        draw_date = datetime.now().strftime("%Y-%m-%d")
    else:
        try:
            d = datetime.strptime(draw_date, "%Y-%m-%d")
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
    """更新日期索引（与之前相同）"""
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
    # 为每个公司获取数据
    for company_key, pid in COMPANY_MAPPING.items():
        print(f"正在处理 {company_key} (PID: {pid})...")
        raw_data = fetch_from_mcp(pid)
        if raw_data:
            data = parse_mcp_data(pid, raw_data)
            save_json(company_key, data)
        else:
            print(f"❌ {company_key} 获取失败")

    update_dates_index()

if __name__ == "__main__":
    main()
