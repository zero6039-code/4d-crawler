// scripts/scraper/damacai.js
const fetch = require('node-fetch');
const { JSDOM } = require('jsdom');
const fs = require('fs');
const path = require('path');

const defaultData = {
  draw_date: "----",
  global_draw_no: "----",
  "1st": "----",
  "2nd": "----",
  "3rd": "----",
  special: Array(10).fill("----"),
  consolation: Array(10).fill("----"),
  draw_info: "----"
};

async function fetchDamacaiResults() {
  try {
    console.log('🔄 步骤 1: 获取开奖日期列表...');
    
    const datesResponse = await fetch('https://www.damacai.com.my/ListPastResult', {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
      }
    });
    
    if (!datesResponse.ok) {
      throw new Error(`获取日期失败：HTTP ${datesResponse.status}`);
    }
    
    const datesData = await datesResponse.json();
    let drawDates = datesData.drawdate.trim().split(' ');
    drawDates = drawDates.sort((a, b) => b.localeCompare(a));
    
    console.log(`📅 前 5 个日期：${drawDates.slice(0, 5).join(', ')}`);
    
    if (!drawDates || drawDates.length === 0) {
      throw new Error('没有获取到开奖日期');
    }
    
    const latestDate = drawDates[0];
    console.log(`📅 最新开奖日期：${latestDate}`);
    
    console.log('🔄 步骤 2: 获取结果文件链接...');
    const linkResponse = await fetch(`https://www.damacai.com.my/callpassresult?pastdate=${latestDate}`, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'cookiesession': '363'
      }
    });
    
    if (!linkResponse.ok) {
      throw new Error(`获取链接失败：HTTP ${linkResponse.status}`);
    }
    
    const linkData = await linkResponse.json();
    const resultUrl = linkData.link;
    
    if (!resultUrl) {
      throw new Error('没有获取到结果链接');
    }
    
    console.log(`🔗 结果链接：${resultUrl}`);
    
    console.log('🔄 步骤 3: 获取 API 数据（特别奖/安慰奖）...');
    const resultResponse = await fetch(resultUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
      }
    });
    
    if (!resultResponse.ok) {
      throw new Error(`获取数据失败：HTTP ${resultResponse.status}`);
    }
    
    const resultData = await resultResponse.json();
    console.log('✅ API 数据获取成功');
    
    // 🔧 步骤 4: 从官网页面爬取实际 4D 号码
    console.log('🔄 步骤 4: 从官网页面获取 4D 号码...');
    const webPrizes = await fetchPrizesFromWeb();
    
    return parseDamacaiData(resultData, latestDate, webPrizes);
    
  } catch (error) {
    console.error(`❌ 获取失败：${error.message}`);
    return defaultData;
  }
}

// 🔧 从官网页面爬取实际 4D 号码
async function fetchPrizesFromWeb() {
  try {
    const url = 'https://www.damacai.com.my/past-draw-result';
    
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html'
      }
    });
    
    if (!response.ok) {
      console.log('⚠️ 网页获取失败');
      return null;
    }
    
    const html = await response.text();
    const dom = new JSDOM(html);
    const doc = dom.window.document;
    
    let firstPrize = null;
    let secondPrize = null;
    let thirdPrize = null;
    
    // 🔍 方法 1: 查找所有 prize-number 元素，根据附近文字判断
    const prizeElements = doc.querySelectorAll('.prize-number');
    
    for (const el of prizeElements) {
      const number = el.textContent?.trim();
      
      // 只处理 4 位数字
      if (!/^\d{4}$/.test(number)) continue;
      
      // 获取父元素和附近内容
      const parent = el.parentElement;
      const grandParent = parent?.parentElement;
      
      // 查找附近的 "1st", "2nd", "3rd" 文字
      const nearbyText = (
        parent?.textContent + 
        grandParent?.textContent + 
        el.previousElementSibling?.textContent
      ).toLowerCase() || '';
      
      // 🔧 关键：根据附近文字判断是第几奖
      if (!firstPrize && (nearbyText.includes('1st') || nearbyText.includes('first'))) {
        firstPrize = number;
        console.log('✅ 找到 1st Prize:', number);
      } else if (!secondPrize && (nearbyText.includes('2nd') || nearbyText.includes('second'))) {
        secondPrize = number;
        console.log('✅ 找到 2nd Prize:', number);
      } else if (!thirdPrize && (nearbyText.includes('3rd') || nearbyText.includes('third'))) {
        thirdPrize = number;
        console.log('✅ 找到 3rd Prize:', number);
      }
    }
    
    // 🔍 方法 2: 尝试查找包含 "1st Prize" 等的容器
    if (!firstPrize || !secondPrize || !thirdPrize) {
      const allDivs = doc.querySelectorAll('div, span, p');
      for (const div of allDivs) {
        const text = div.textContent?.toLowerCase() || '';
        if (text.includes('1st prize') || text.includes('first prize')) {
          const match = div.innerHTML.match(/class="prize-number"[^>]*>(\d{4})</);
          if (match && !firstPrize) firstPrize = match[1];
        } else if (text.includes('2nd prize') || text.includes('second prize')) {
          const match = div.innerHTML.match(/class="prize-number"[^>]*>(\d{4})</);
          if (match && !secondPrize) secondPrize = match[1];
        } else if (text.includes('3rd prize') || text.includes('third prize')) {
          const match = div.innerHTML.match(/class="prize-number"[^>]*>(\d{4})</);
          if (match && !thirdPrize) thirdPrize = match[1];
        }
      }
    }
    
    console.log('📊 网页爬取结果:', { firstPrize, secondPrize, thirdPrize });
    
    return { firstPrize, secondPrize, thirdPrize };
  } catch (error) {
    console.log('⚠️ 网页爬取失败:', error.message);
    return null;
  }
}

function parseDamacaiData(data, drawDate, webPrizes) {
  const formattedDate = `${drawDate.substring(6,8)}-${drawDate.substring(4,6)}-${drawDate.substring(0,4)}`;
  
  // 🔧 优先使用网页爬取的 4D 号码
  const firstPrize = webPrizes?.firstPrize || "----";
  const secondPrize = webPrizes?.secondPrize || "----";
  const thirdPrize = webPrizes?.thirdPrize || "----";
  
  // 特别奖 (starterList) - 从 API 获取
  let special = data.starterList || data.starterHorseList || [];
  if (!Array.isArray(special)) special = [];
  
  // 安慰奖 (consolidateList) - 从 API 获取
  let consolation = data.consolidateList || [];
  if (!Array.isArray(consolation)) consolation = [];
  
  // 过滤并填充到 10 个
  special = special.filter(s => s && s !== "-" && s !== "null").slice(0, 10);
  consolation = consolation.filter(c => c && c !== "-" && c !== "null").slice(0, 10);
  
  while (special.length < 10) special.push("----");
  while (consolation.length < 10) consolation.push("----");
  
  console.log('📊 解析后的头奖:', firstPrize);
  console.log('📊 解析后的二奖:', secondPrize);
  console.log('📊 解析后的三奖:', thirdPrize);
  console.log('📊 解析后的特别奖:', special);
  console.log('📊 解析后的安慰奖:', consolation);
  
  return {
    draw_date: formattedDate,
    global_draw_no: data.drawNo || "----",
    "1st": firstPrize,
    "2nd": secondPrize,
    "3rd": thirdPrize,
    special: special,
    consolation: consolation,
    draw_info: (data.drawNo) ? `(${getDayName(formattedDate)}) ${formattedDate} #${data.drawNo}` : "----"
  };
}

function getDayName(dateStr) {
  const [day, month, year] = dateStr.split('-');
  const date = new Date(`${year}-${month}-${day}`);
  const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  return days[date.getDay()];
}

async function main() {
  console.log(`🔄 [${new Date().toLocaleString('zh-MY')}] 开始抓取 DAMACAI 数据...`);
  
  const results = await fetchDamacaiResults();
  
  const outputPath = path.join(__dirname, '../../docs/data/damacai.json');
  fs.writeFileSync(outputPath, JSON.stringify(results, null, 2));
  
  console.log(`✅ [${new Date().toLocaleString('zh-MY')}] DAMACAI 数据已更新`);
  console.log('📄 输出文件:', outputPath);
  console.log('📊 生成数据:', JSON.stringify(results, null, 2));
}

main();
