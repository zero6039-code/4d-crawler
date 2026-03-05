def extract_singapore_toto_4dmoon(soup):
    print("🔍 开始解析 Singapore Toto 页面...")

    # 打印页面标题
    if soup.title:
        print(f"📄 页面标题: {soup.title.get_text(strip=True)}")
    else:
        print("⚠️ 页面无标题")

    # 打印前2000个字符的 HTML 预览
    print("📄 页面 HTML 预览（前2000字符）:")
    print(soup.prettify()[:2000])

    data = {
        "draw_date": "",
        "draw_no": "",
        "winning_numbers": [],
        "prize_table": []
    }

    # 尝试多种方式查找标题
    toto_header = None
    # 方法1：精确查找
    toto_header = soup.find("td", string=re.compile(r"Singapore\s*Toto", re.I))
    if not toto_header:
        # 方法2：查找所有包含 "Singapore" 和 "Toto" 的 td
        for td in soup.find_all("td"):
            text = td.get_text(strip=True)
            if "Singapore" in text and "Toto" in text:
                toto_header = td
                print(f"✅ 通过宽松匹配找到标题: {text}")
                break
    if not toto_header:
        print("❌ 错误：所有方法均未找到 'Singapore Toto' 标题")
        return None

    print(f"✅ 找到标题: {toto_header.get_text(strip=True)}")
    # ... 后续提取逻辑保持不变 ...
