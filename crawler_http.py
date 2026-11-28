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
MAX_BYTES = 2 * 1024 * 1024

# ---------- 共享 HTTP 会话（连接池 + 指数退避） ----------
def make_session():
    s = requests.Session()
    s.mount("https://", HTTPAdapter(max_retries=Retry(
        total=2, backoff_factor=1.0, backoff_max=10,
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


# ---------- 增强版请求函数（支持重试、会话、完整头）----------
def fetch_html(url, max_retries=2, timeout=(5, 15), deadline=60):
    t0 = time.monotonic()
    session = SESSION

    if "gdlotto.net" in url:
        try:
            print("🌐 先访问 gdlotto.net 首页以获取 cookies...")
            session.get("https://gdlotto.net/", timeout=timeout)
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ 访问首页失败，但仍尝试请求目标URL: {e}")

    for attempt in range(max_retries):
        if time.monotonic() - t0 > deadline:
            return None
        try:
            print(f"🌐 正在请求 {url} (尝试 {attempt+1}/{max_retries})")
            with session.get(url, timeout=timeout, stream=True) as r:
                print(f"  状态码: {r.status_code}")
                r.raise_for_status()
                buf = bytearray()
                while True:
                    # read1：收到多少就返回多少，才能在慢速滴灌时按时检查总时限
                    chunk = r.raw.read1(65536, decode_content=True)
                    if not chunk:
                        break
                    buf += chunk
                    if len(buf) > MAX_BYTES:
                        raise ValueError("响应超过上限")
                    if time.monotonic() - t0 > deadline:
                        raise ValueError("超过总时限")
                return bytes(buf).decode("utf-8", "replace")
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"❌ 抓取失败: {e}")
            if attempt < max_retries - 1:
                print(f"⏳ 等待 {attempt+1} 秒后重试...")
                time.sleep(2 ** attempt)
            else:
                return None
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
