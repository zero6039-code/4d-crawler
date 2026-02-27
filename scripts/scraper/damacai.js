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
    
    console.log('🔄 步骤 4: 从官网页面获取 4D 号码...');
    const webPrizes = await fetchPrizesFromWeb();
    
    return parseDamacaiData(resultData, latestDate, webPrizes);
    
  } catch (error) {
    console.error(`❌ 获取失败：${error.message}`);
    return defaultData;
  }
}

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
    
    // 🔍 方法 1: 只查找 1+3D 区域，排除 SUPER 1+3D
    const game1Plus3D = doc.querySelector('.game1Plus3D, [class*="1+3D"], [class*="1-3D"]');
    
    if (game1Plus3D) {
      console.log('✅ 找到 1+3D 游戏区域');
      
      const labels = game1Plus3D.querySelectorAll('.prize-label');
      
      for (const label of labels) {
        const labelText = label.textContent?.trim().toLowerCase() || '';
        const parent = label.parentElement;
        
        let numberEl = parent?.querySelector('.prize-number');
        
        if (!numberEl) {
          const row = parent?.closest('.row');
          if (row) {
            numberEl = row.querySelector('.prize-number');
          }
        }
        
        if (!numberEl) continue;
        
        const number = numberEl.textContent?.trim();
        
        if (!/^\d{4}$/.test(number)) continue;
        
        console.log('📍 找到:', labelText, '=', number);
        
        if (!firstPrize && labelText.includes('1st')) {
          firstPrize = number;
        } else if (!secondPrize && labelText.includes('2nd')) {
          secondPrize = number;
        } else if (!thirdPrize && labelText.includes('3rd')) {
          thirdPrize = number;
        }
      }
    }
    
    // 🔍 方法 2: 查找 topPrize_0 容器（排除 SUPER 区域）
    if (!firstPrize || !secondPrize || !thirdPrize) {
      const topPrizeRows = doc.querySelectorAll('.topPrize_0');
      
      console.log('🔍 找到 topPrize_0 容器数量:', topPrizeRows.length);
      
      for (const row of topPrizeRows) {
        const superArea = row.closest('[class*="super"], [class*="SUPER"]');
        if (superArea) {
          console.log('⚠️ 跳过 SUPER 区域');
          continue;
        }
        
        const labelEl = row.querySelector('.prize-label');
        const numberEl = row.querySelector('.prize-number');
        
        if (!labelEl || !numberEl) continue;
        
        const labelText = labelEl.textContent?.trim().toLowerCase() || '';
        const number = numberEl.textContent?.trim();
        
        if (!/^\d{4}$/.test(number)) continue;
        
        console.log('📍 topPrize_0 找到:', labelText, '=', number);
        
        if (!firstPrize && labelText.includes('1st')) {
          firstPrize = number;
        } else if (!secondPrize && labelText.includes('2nd')) {
          secondPrize = number;
        } else if (!thirdPrize && labelText.includes('3rd')) {
          thirdPrize = number;
        }
      }
    }
    
    // 🔍 方法 3: 按页面顺序查找前 3 个 prize-number（排除 SUPER 区域）
    if (!firstPrize || !secondPrize || !thirdPrize) {
      const prizeNumbers = doc.querySelectorAll('.prize-number');
      let index = 0;
      
      console.log('🔍 方法 3: 找到 prize-number 总数:', prizeNumbers.length);
      
      for (const el of prizeNumbers) {
        const superArea = el.closest('[class*="super"], [class*="SUPER"]');
        if (superArea) {
          console.log('⚠️ 跳过 SUPER 区域的号码:', el.textContent?.trim());
          continue;
        }
        
        if (el.hasAttribute('data-history-prize')) {
          console.log('⚠️ 跳过历史数据:', el.textContent?.trim());
          continue;
        }
        
        const number = el.textContent?.trim();
        if (!/^\d{4}$/.test(number)) continue;
        
        console.log('📍 方法 3 找到:', number);
        
        if (index === 0 && !firstPrize) firstPrize = number;
        else if (index === 1 && !secondPrize) secondPrize = number;
        else if (index === 2 && !thirdPrize) thirdPrize = number;
        
        index++;
        if (index >= 3) break;
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
  
  const firstPrize = webPrizes?.firstPrize || "----";
  const secondPrize = webPrizes?.secondPrize || "----";
  const thirdPrize = webPrizes?.thirdPrize || "----";
  
  let special = data.starterList || data.starterHorseList || [];
  if (!Array.isArray(special)) special = [];
  
  let consolation = data.consolidateList || [];
  if (!Array.isArray(consolation)) consolation = [];
  
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
