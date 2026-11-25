import re
import time
import requests
from datetime import datetime, timezone, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ========== 路径统一配置 ==========

# ---------- 配置 ----------
URL_4D4D = "https://4d4d.co/"
URL_DATO4D = "https://www.dato4d.com/liveos.json"

# ---------- 共享 HTTP 会话（连接池 + 指数退避） ----------
def make_session():
    s = requests.Session()
    s.mount("https://", HTTPAdapter(max_retries=Retry(
        total=4, backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",), respect_retry_after_header=True)))
    s.headers["User-Agent"] = "Mozilla/5.0 (compatible; 4d-crawler/2.0)"
    return s

SESSION = make_session()

# ---------- 日期转换辅助函数 ----------
def dmy_to_ymd(date_str):
    if not date_str or date_str == '----':
        return None
    try:
        d = datetime.strptime(date_str, "%d-%m-%Y")
        return d.strftime("%Y-%m-%d")
    except ValueError:
        return None

def ymd_to_dmy(date_str):
    if not date_str:
        return ''
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return d.strftime("%d-%m-%Y")
    except ValueError:
        return date_str

# ---------- 增强版请求函数（支持重试、会话、完整头）----------
def fetch_html(url, max_retries=3, timeout=15):
    session = SESSION
    
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
            r.encoding = "utf-8"
            r.raise_for_status()
            return r.text
        except requests.exceptions.RequestException as e:
            print(f"❌ 抓取失败: {e}")
            if attempt < max_retries - 1:
                print(f"⏳ 等待 {attempt+1} 秒后重试...")
                time.sleep(2 ** attempt)
            else:
                return None
    return None

def find_parent_table(element):
    while element and element.name != 'table':
        element = element.parent
    return element

def parse_4dmoon_date(date_str):
    try:
        d = datetime.strptime(date_str.strip(), "%d-%b-%Y")
        return d.strftime("%d-%m-%Y")
    except ValueError:
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
