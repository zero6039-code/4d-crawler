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
    """官方源优先；403/缺奖时自动切 mkt88 / i.check4d.today。"""
    now = now or datetime.now(MYT)

    def _page(url):
        r = session.get(url, timeout=15, headers={"User-Agent": UA})
        r.raise_for_status()
        t = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", r.text, flags=re.I | re.S)
        t = re.sub(r"<[^>]+>", " ", t).replace("&nbsp;", " ")
        return re.sub(r"\s+", " ", t)

    def _paged_data(text, threshold, date_re, no_re, first_re, second_re, third_re, sp_re, co_re):
        dm = re.search(date_re, text, re.I)
        if not dm:
            return {}
        ymd = to_ymd(dm.group(1))
        if not ymd or ymd < threshold:
            return {}

        def one(pattern):
            m = re.search(pattern, text, re.I)
            return m.group(1) if m else ""

        first, second, third = one(first_re), one(second_re), one(third_re)
        if not (first and second and third):
            return {}
        sp = re.search(sp_re, text, re.I | re.S)
        co = re.search(co_re, text, re.I | re.S)
        no = re.search(no_re, text, re.I)
        return {
            "draw_date": ymd,
            "draw_no": no.group(1) if no else "",
            "draw_time": "7:30 PM",
            "1st": first,
            "2nd": second,
            "3rd": third,
            "special": re.findall(r"\d{4}", sp.group(1)) if sp else [],
            "consolation": re.findall(r"\d{4}", co.group(1)) if co else [],
        }

    for day in (now, now - timedelta(days=1)):
        ds = day.strftime("%Y-%m-%d")
        ts = int(time.time() * 1000)
        url = (f"https://api.hari4d.com/DrawResultL/GetDrawResult"
               f"?date={ds}T19:30:00&nocache={ts}&_={ts}")
        try:
            r = session.get(url, timeout=15, headers={"User-Agent": UA, "Referer": "https://www.hari4d.com/"})
            r.raise_for_status()
            j = r.json()
        except Exception as e:
            print(f"⚠️ Lucky HariHari 官方源 {ds} 抓取失败: {e}")
            j = {}
        if j.get("prize1"):
            special = [j.get(k) for k in ("prizeA", "prizeB", "prizeC", "prizeE",
                                          "prizeF", "prizeH", "prizeL", "prizeN",
                                          "prizeO", "prizeP")]
            cons = [j.get(k) for k in ("prizeQ", "prizeR", "prizeS", "prizeT",
                                       "prizeU", "prizeV", "prizeW")]
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

        sources = (
            ("mkt88", "https://www.mkt88.my/result/lucky-harihari",
             r"Date:\s*(\d{2}-\d{2}-\d{4})", r"Draw No:\s*(\d+)",
             r"1st Prize 首奖\s*(\d{4})", r"2nd Prize 二奖\s*(\d{4})",
             r"3rd Prize 三奖\s*(\d{4})",
             r"Special 特别奖(.*?)Consolation 安慰奖",
             r"Consolation 安慰奖(.*?)Jackpot Pool"),
            ("check4d", "https://i.check4d.today/",
             r"LUCKY HARI HARI 4D.*?(\d{2}-\d{2}-\d{4})", r"No:\s*(\d+)",
             r"1st Prize:\s*[A-Z]\s*(\d{4})", r"2nd Prize:\s*[A-Z]\s*(\d{4})",
             r"3rd Prize:\s*[A-Z]\s*(\d{4})",
             r"Special\s*([A-M]\s*(?:\d{4}|----)\s*)+",
             r"Consolation\s*([N-W]\s*(?:\d{4}|----)\s*)+"),
        )
        for name, url_fb, date_re, no_re, r1, r2, r3, sp_re, co_re in sources:
            try:
                data = _paged_data(_page(url_fb), ds, date_re, no_re, r1, r2, r3, sp_re, co_re)
            except Exception as e:
                print(f"⚠️ Lucky HariHari {name} 抓取失败: {e}")
                continue
            if data:
                print(f"✅ Lucky HariHari 改用备用源 {name} ({data['draw_date']})")
                return data
    return {}
