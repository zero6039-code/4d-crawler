import re, time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from crawler_utils import to_ymd, to_dmy

MYT = timezone(timedelta(hours=8))
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

def _money(s):
    digits = re.sub(r'[^0-9]', '', s or '')
    return f"${int(digits):,}" if digits else '-'

def scrape_singapore_toto(min_date=None):
    """从 4dpredict.app 抓取 SGT；只返回比 min_date 更新的一期。"""
    try:
        r = requests.get("https://www.4dpredict.app/singaporetoto",
                         headers={"User-Agent": UA}, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"⚠️ Singapore Toto 备用源抓取失败: {e}")
        return None

    soup = BeautifulSoup(r.text, 'html.parser')
    best = None
    for col in soup.find_all('div', class_='column is-one-third'):
        header = col.find('td', class_='s4d')
        if not header:
            continue
        txt = header.get_text(' ', strip=True)
        dm = re.search(r'\d{4}-\d{2}-\d{2}', txt)
        gm = re.search(r'(\d+)\s*$', txt)
        if not dm or not gm:
            continue
        ymd = dm.group(0)
        if min_date and ymd <= min_date:
            continue
        row = col.find('tr', class_='is-size-3')
        if not row:
            continue
        nums = [s.get_text(strip=True) for s in row.find_all('span')]
        if len(nums) < 7:
            continue

        shares = {}
        for table in col.find_all('table'):
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                label = tds[0].get_text(strip=True)
                if len(tds) == 3 and re.fullmatch(r'Group\s+\d+', label):
                    shares[label] = [
                        _money(tds[1].get_text()), tds[2].get_text(strip=True)]

        data = {
            "draw_date": to_dmy(ymd),
            "draw_no": gm.group(1),
            "winning_numbers": nums[:7],
            "prize_table": [[g, v[0], v[1]] for g, v in shares.items()],
        }
        p = col.find(string=re.compile(r'Prize:'))
        if p:
            pm = re.search(r'\$([\d,]+)', p.parent.get_text(strip=True))
            if pm:
                data["prize"] = _money(pm.group(1))
        if best is None or ymd > best[0]:
            best = (ymd, data)
    return best[1] if best else None

def fetch_lucky_hari(session, now=None):
    """今天 403/失败自动回退昨天，返回现有 schema 或 {}。"""
    now = now or datetime.now(MYT)
    for day in (now, now - timedelta(days=1)):
        ds = day.strftime('%Y-%m-%d')
        ts = int(time.time() * 1000)
        url = (f"https://api.hari4d.com/DrawResultL/GetDrawResult"
               f"?date={ds}T19:30:00&nocache={ts}&_={ts}")
        try:
            r = session.get(url, timeout=15, headers={"User-Agent": UA})
            r.raise_for_status()
            j = r.json()
        except Exception as e:
            print(f"⚠️ Lucky HariHari {ds} 抓取失败: {e}")
            continue
        if j.get('prize1') and j.get('isDone') is not False:
            special = [j.get(k) for k in ('prizeA','prizeB','prizeC','prizeE',
                                          'prizeF','prizeH','prizeL','prizeN',
                                          'prizeO','prizeP')]
            cons = [j.get(k) for k in ('prizeQ','prizeR','prizeS','prizeT',
                                       'prizeU','prizeV','prizeW')]
            return {
                "draw_date": str(j.get("drawDate", "")).split("T")[0],
                "draw_no": "",
                "draw_time": "7:30 PM",
                "1st": j.get("prize1", ""),
                "2nd": j.get("prize2", ""),
                "3rd": j.get("prize3", ""),
                "special": [n for n in special if n and n != "----"],
                "consolation": [n for n in cons if n and n != "----"],
            }
    return {}
