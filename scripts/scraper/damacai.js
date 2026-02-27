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
    
    console.log(`🔗 结果链接：${resultUrl.substring(0, 80)}...`);
    
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
    console.log('📊 API 特别奖:', resultData.starterList || resultData.starterHorseList);
    console.log('📊 API 安慰奖:', resultData.consolidateList);
    
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
    console.log('🌐 请求 URL:', url);
    
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html'
      }
    });
    
    console.log('📡 响应状态:', response.status);
    
    if (!response.ok) {
      console.log('⚠️ 网页获取失败');
      return null;
    }
    
    const html = await response.text();
    console.log('📄 HTML 长度:', html.length);
    
    const dom = new JSDOM(html);
    const doc = dom.window.document;
    
    let firstPrize = null;
    let secondPrize = null;
    let thirdPrize = null;
    
    // 🔍 方法 1: 查找所有 prize-number 元素
    const prizeNumbers = doc.querySelectorAll('.prize-number');
    console.log('🔍 找到 .prize-number 元素数量:', prizeNumbers.length);
    
    for (let i = 0; i < prizeNumbers.length; i++) {
      const el = prizeNumbers[i];
      const number = el.textContent?.trim();
      const classList = el.className;
      const hasHistory = el.hasAttribute('data-history-prize');
      
      console.log(`  [${i}] 号码: ${number}, class: ${classList}, 历史数据: ${hasHistory}`);
      
      // 跳过非 4 位数字
      if (!/^\d{4}$/.test(number)) continue;
      
      // 跳过历史数据
      if (hasHistory) {
        console.log(`    ⚠️ 跳过历史数据`);
        continue;
      }
      
      // 获取附近的 label 文字
      const parent = el.parentElement;
      const nearbyText = (parent?.textContent || '').toLowerCase();
      console.log(`    附近文字: ${nearbyText.substring(0, 50)}...`);
      
      if (!firstPrize && (nearbyText.includes('1st') || nearbyText.includes('first'))) {
        firstPrize = number;
        console.log(`    ✅ 设为 1st Prize`);
      } else if (!secondPrize && (nearbyText.includes('2nd') || nearbyText.includes('second'))) {
        secondPrize = number;
        console.log(`    ✅ 设为 2nd Prize`);
      } else if (!thirdPrize && (nearbyText.includes('3rd') || nearbyText.includes('third'))) {
        thirdPrize = number;
        console.log(`    ✅ 设为 3rd Prize`);
      }
    }
    
    // 🔍 方法 2: 直接取前 3 个有效的 4 位数字
    if (!firstPrize || !secondPrize || !thirdPrize) {
      console.log('🔍 方法 2: 尝试直接取前 3 个 4 位数字');
      
      let index = 0;
      for (const el of prizeNumbers) {
        const number = el.textContent?.trim();
        
        if (!/^\d{4}$/.test(number)) continue;
        if (el.hasAttribute('data-history-prize')) continue;
        
        console.log(`  方法 2 找到: ${number}`);
        
        if (index === 0 && !firstPrize) firstPrize = number;
        else if (index === 1 && !secondPrize) secondPrize = number;
        else if (index === 2 && !thirdPrize) thirdPrize = number;
        
        index++;
        if (index >= 3) break;
      }
    }
    
    // 🔍 方法 3: 从 HTML 文本中提取所有 4 位数字
    if (!firstPrize || !secondPrize || !thirdPrize) {
      console.log('🔍 方法 3: 从 HTML 文本提取 4 位数字');
      
      const allText = doc.body.textContent || '';
      const fourDigitNumbers = allText.match(/\b\d{4}\b/g) || [];
      console.log(`  找到 ${fourDigitNumbers.length} 个 4 位数字`);
      console.log(`  前 20 个: ${fourDigitNumbers.slice(0, 20)}`);
      
      // 过滤掉年份
      const currentYear = new Date().getFullYear();
      const validNumbers = fourDigitNumbers.filter(n => {
        const num = parseInt(n);
        return num < 1900 || num > (currentYear + 1);
      });
      
      console.log(`  过滤后: ${validNumbers.slice(0, 20)}`);
      
      if (!firstPrize && validNumbers[0]) firstPrize = validNumbers[0];
      if (!secondPrize && validNumbers[1]) secondPrize = validNumbers[1];
      if (!thirdPrize && validNumbers[2]) thirdPrize = validNumbers[2];
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
