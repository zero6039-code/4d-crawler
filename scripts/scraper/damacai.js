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
    
    // 按日期降序排序（最新的在前面）
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
    
    console.log('🔄 步骤 3: 获取开奖数据...');
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
    console.log('📊 原始数据:', JSON.stringify(resultData, null, 2));
    
    // 🔧 步骤 4: 从官网页面获取实际 4D 号码
    console.log('🔄 步骤 4: 从官网页面获取 4D 号码...');
    const webPrizes = await fetchPrizesFromWeb(latestDate);
    
    return parseDamacaiData(resultData, latestDate, webPrizes);
    
  } catch (error) {
    console.error(`❌ 获取失败：${error.message}`);
    return defaultData;
  }
}

// 🔧 新增：从官网页面爬取实际 4D 号码
async function fetchPrizesFromWeb(drawDate) {
  try {
    const formattedUrlDate = `${drawDate.substring(6,8)}-${drawDate.substring(4,6)}-${drawDate.substring(0,4)}`;
    const url = `https://www.damacai.com.my/past-draw-result`;
    
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html'
      }
    });
    
    if (!response.ok) {
      console.log('⚠️ 网页获取失败，使用 API 数据');
      return null;
    }
    
    const html = await response.text();
    const dom = new JSDOM(html);
    const doc = dom.window.document;
    
    // 🔍 尝试多种选择器获取 4D 号码
    let firstPrize = null;
    let secondPrize = null;
    let thirdPrize = null;
    
    // 方法 1: 查找包含 prize 或 number 的元素
    const allElements = doc.querySelectorAll('*');
    for (const el of allElements) {
      const text = el.textContent?.trim();
      // 4D 号码是 4 位数字
      if (/^\d{4}$/.test(text)) {
        const parent = el.parentElement;
        const grandParent = parent?.parentElement;
        
        // 检查附近是否有 "1st", "2nd", "3rd" 等文字
        const nearbyText = (parent?.textContent + grandParent?.textContent || '').toLowerCase();
        
        if (nearbyText.includes('1st') || nearbyText.includes('first')) {
          firstPrize = text;
        } else if (nearbyText.includes('2nd') || nearbyText.includes('second')) {
          secondPrize = text;
        } else if (nearbyText.includes('3rd') || nearbyText.includes('third')) {
          thirdPrize = text;
        }
      }
    }
    
    // 方法 2: 尝试常见 class 名
    if (!firstPrize) {
      firstPrize = doc.querySelector('.first-prize')?.textContent?.trim() ||
                   doc.querySelector('[class*="first"]')?.textContent?.trim() ||
                   doc.querySelector('[data-prize="1"]')?.textContent?.trim();
    }
    if (!secondPrize) {
      secondPrize = doc.querySelector('.second-prize')?.textContent?.trim() ||
                    doc.querySelector('[class*="second"]')?.textContent?.trim() ||
                    doc.querySelector('[data-prize="2"]')?.textContent?.trim();
    }
    if (!thirdPrize) {
      thirdPrize = doc.querySelector('.third-prize')?.textContent?.trim() ||
                   doc.querySelector('[class*="third"]')?.textContent?.trim() ||
                   doc.querySelector('[data-prize="3"]')?.textContent?.trim();
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
  
  // 🔧 优先使用网页爬取的 4D 号码，如果没有则用 API 数据
  const firstPrize = webPrizes?.firstPrize || data.firstPrize4D || data.p1HorseNo || "----";
  const secondPrize = webPrizes?.secondPrize || data.secondPrize4D || data.p2HorseNo || "----";
  const thirdPrize = webPrizes?.thirdPrize || data.thirdPrize4D || data.p3HorseNo || "----";
  
  // 特别奖 (starterList)
  let special = data.starterList || data.starterHorseList || data.Special || data.special || [];
  if (!Array.isArray(special)) special = [];
  
  // 安慰奖 (consolidateList)
  let consolation = data.consolidateList || data.Consolation || data.consolation || [];
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
    global_draw_no: data.drawNo || data.DrawNo || data.draw_no || "----",
    "1st": firstPrize,
    "2nd": secondPrize,
    "3rd": thirdPrize,
    special: special,
    consolation: consolation,
    draw_info: (data.drawNo || data.DrawNo || data.draw_no) 
      ? `(${getDayName(formattedDate)}) ${formattedDate} #${data.drawNo || data.DrawNo || data.draw_no}`
      : "----"
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
