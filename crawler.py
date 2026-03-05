# ========== 最终修复版 SABAH88 沙巴萬字 LOTTO 提取函数 ==========
def extract_sabah_lotto_from_4dlatest(soup):
    """
    从 https://4dlatest.org/ 精确提取 "SABAH88 沙巴萬字 LOTTO" 数据
    """
    print("🔍 正在从 4dlatest.org 提取 SABAH88 沙巴萬字 LOTTO 数据...")
    data = {
        "draw_date": "",
        "draw_no": "",
        "winning_numbers": [],
        "jackpot1": "",
        "jackpot2": ""
    }

    # 1. 精确定位标题所在单元格（使用完整标题文本，忽略大小写）
    # 注意：标题是 "SABAH88 沙巴萬字 LOTTO"，中间可能包含空格或换行
    header = soup.find('td', string=re.compile(r"SABAH88\s*沙巴萬字\s*LOTTO", re.IGNORECASE))
    if not header:
        # 备选方案：如果上面没找到，尝试更宽松的匹配（可能页面显示为“黄字”）
        header = soup.find('td', string=re.compile(r"SABAH88.*LOTTO", re.IGNORECASE))
        if header:
            print("⚠️ 通过宽松匹配找到标题，请确认页面显示是否正确")
        else:
            print("❌ 未找到 'SABAH88 沙巴萬字 LOTTO' 标题")
            return None

    # 打印找到的标题文本，方便调试
    print(f"✅ 找到标题: {header.get_text(strip=True)}")

    # 2. 获取标题所在的表格
    table = header.find_parent("table")
    if not table:
        print("❌ 未找到包含标题的表格")
        return None

    # 3. 从标题行提取日期和期号
    header_text = header.get_text(" ", strip=True)
    print(f"📅 标题文本: {header_text}")

    # 匹配日期 (格式: DD/MM/YYYY)
    date_match = re.search(r"(\d{2}/\d{2}/\d{4})", header_text)
    if date_match:
        try:
            d = datetime.strptime(date_match.group(1), "%d/%m/%Y")
            data["draw_date"] = d.strftime("%d-%m-%Y")
            print(f"  ✅ 提取到日期: {data['draw_date']}")
        except Exception as e:
            print(f"  ⚠️ 日期解析失败: {e}")

    # 匹配期号 (格式: 4165/26)
    no_match = re.search(r"(\d+/\d+)", header_text)
    if no_match:
        data["draw_no"] = no_match.group(1)
        print(f"  ✅ 提取到期号: {data['draw_no']}")

    # 4. 遍历表格行提取开奖号码和奖池
    rows = table.find_all("tr")
    for row in rows:
        row_text = row.get_text()
        cells = row.find_all("td")

        # 提取开奖号码行（包含 "+"）
        if "+" in row_text:
            numbers = []
            for cell in cells:
                text = cell.get_text(strip=True)
                if text.isdigit():
                    numbers.append(text)
                elif text == "+":
                    pass
            if numbers:
                data["winning_numbers"] = numbers
                print(f"✅ 提取到开奖号码: {' '.join(numbers)}")
            continue  # 号码行处理完后继续下一行

        # 提取 Jackpot 1 (精确匹配)
        if "Jackpot 1" in row_text:
            for cell in cells:
                text = cell.get_text(strip=True)
                # 匹配金额，例如 "741,317.34"
                amount_match = re.search(r'([\d,]+(?:\.\d+)?)', text)
                if amount_match:
                    data["jackpot1"] = amount_match.group(1)
                    print(f"  ✅ Jackpot 1: {data['jackpot1']}")
                    break
            # 如果当前行没找到，检查下一行（有时金额在下一行）
            if not data["jackpot1"]:
                next_row = row.find_next_sibling("tr")
                if next_row:
                    next_cells = next_row.find_all("td")
                    for cell in next_cells:
                        text = cell.get_text(strip=True)
                        amount_match = re.search(r'([\d,]+(?:\.\d+)?)', text)
                        if amount_match:
                            data["jackpot1"] = amount_match.group(1)
                            print(f"  ✅ Jackpot 1 (下一行): {data['jackpot1']}")
                            break

        # 提取 Jackpot 2
        if "Jackpot 2" in row_text:
            for cell in cells:
                text = cell.get_text(strip=True)
                amount_match = re.search(r'([\d,]+(?:\.\d+)?)', text)
                if amount_match:
                    data["jackpot2"] = amount_match.group(1)
                    print(f"  ✅ Jackpot 2: {data['jackpot2']}")
                    break
            if not data["jackpot2"]:
                next_row = row.find_next_sibling("tr")
                if next_row:
                    next_cells = next_row.find_all("td")
                    for cell in next_cells:
                        text = cell.get_text(strip=True)
                        amount_match = re.search(r'([\d,]+(?:\.\d+)?)', text)
                        if amount_match:
                            data["jackpot2"] = amount_match.group(1)
                            print(f"  ✅ Jackpot 2 (下一行): {data['jackpot2']}")
                            break

    return data
