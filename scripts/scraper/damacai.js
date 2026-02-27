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
    
    // 🔍 方法：查找所有 4 位数字，根据上下文判断是第几奖
    const allText = doc.body.textContent || '';
    const fourDigitRegex = /\b\d{4}\b/g;
    let matches;
    
    // 获取所有 4 位数字及其位置
    const numberPositions = [];
    while ((matches = fourDigitRegex.exec(allText)) !== null) {
      // 获取数字前后 100 字符的上下文
      const start = Math.max(0, matches.index - 100);
      const end = Math.min(allText.length, matches.index + 100);
      const context = allText.substring(start, end).toLowerCase();
      
      numberPositions.push({
        number: matches[0],
        context: context,
        index: matches.index
      });
    }
    
    // 根据上下文判断 1st/2nd/3rd
    for (const item of numberPositions) {
      if (!firstPrize && (item.context.includes('1st') || item.context.includes('first prize'))) {
        firstPrize = item.number;
      } else if (!secondPrize && (item.context.includes('2nd') || item.context.includes('second prize'))) {
        secondPrize = item.number;
      } else if (!thirdPrize && (item.context.includes('3rd') || item.context.includes('third prize'))) {
        thirdPrize = item.number;
      }
    }
    
    // 🔍 备用方法：尝试常见 class 名
    if (!firstPrize) {
      const prizeElements = doc.querySelectorAll('[class*="prize"], [class*="Prize"], [data-prize]');
      for (const el of prizeElements) {
        const text = el.textContent?.trim();
        if (/^\d{4}$/.test(text)) {
          const classText = (el.className || '').toLowerCase();
          if (classText.includes('1st') || classText.includes('first')) {
            firstPrize = text;
          } else if (classText.includes('2nd') || classText.includes('second')) {
            secondPrize = text;
          } else if (classText.includes('3rd') || classText.includes('third')) {
            thirdPrize = text;
          }
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
