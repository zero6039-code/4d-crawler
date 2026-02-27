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
    
    // 🔧 步骤 4: 尝试从第三方获取 1st/2nd/3rd 号码
    console.log('🔄 步骤 4: 获取 1st/2nd/3rd 号码...');
    const prizes = await fetchPrizesFromMultipleSources(latestDate, resultData);
    
    return parseDamacaiData(resultData, latestDate, prizes);
    
  } catch (error) {
    console.error(`❌ 获取失败：${error.message}`);
    return defaultData;
  }
}

// 🔧 从多个数据源获取 1st/2nd/3rd 号码
async function fetchPrizesFromMultipleSources(drawDate, apiData) {
  let firstPrize = null;
  let secondPrize = null;
  let thirdPrize = null;
  
  // 🔍 方法 1: 检查 API 数据中是否有 4D 号码字段
  console.log('🔍 方法 1: 检查 API 数据字段...');
  console.log('📋 API 所有字段:', Object.keys(apiData));
  
  // 尝试各种可能的字段名
  const possibleFields = [
    'firstPrize', 'FirstPrize', 'first_prize', '1st',
    'secondPrize', 'SecondPrize', 'second_prize', '2nd',
    'thirdPrize', 'ThirdPrize', 'third_prize', '3rd',
    'p1', 'p2', 'p3',
    'top1', 'top2', 'top3'
  ];
  
  for (const field of possibleFields) {
    if (!firstPrize && apiData[field] && /^\d{4}$/.test(apiData[field])) {
      firstPrize = apiData[field];
      console.log(`✅ 从 API 字段 ${field} 获取 1st: ${firstPrize}`);
    }
  }
  
  // 🔍 方法 2: 尝试从 live4d2u 获取（第三方聚合网站）
  if (!firstPrize || !secondPrize || !thirdPrize) {
    console.log('🔍 方法 2: 尝试从 live4d2u 获取...');
    try {
      const response = await fetch('https://www.live4d2u.net/', {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
          'Accept': 'text/html'
        }
      });
      
      if (response.ok) {
        const html = await response.text();
        const dom = new JSDOM(html);
        const doc = dom.window.document;
        
        // 查找 DAMACAI 区域
        const damacaiSection = doc.querySelector('[data-company="damacai"], .damacai, [class*="damacai"]');
        
        if (damacaiSection) {
          const numbers = damacaiSection.querySelectorAll('[class*="prize"], [class*="Prize"]');
          let index = 0;
          for (const num of numbers) {
            const text = num.textContent?.trim();
            if (/^\d{4}$/.test(text)) {
              if (index === 0 && !firstPrize) firstPrize = text;
              else if (index === 1 && !secondPrize) secondPrize = text;
              else if (index === 2 && !thirdPrize) thirdPrize = text;
              index++;
            }
          }
        }
        
        if (firstPrize) {
          console.log(`✅ 从 live4d2u 获取：1st=${firstPrize}, 2nd=${secondPrize}, 3rd=${thirdPrize}`);
        }
      }
    } catch (err) {
      console.log('⚠️ live4d2u 获取失败:', err.message);
    }
  }
  
  // 🔍 方法 3: 从 check4d 获取
  if (!firstPrize || !secondPrize || !thirdPrize) {
    console.log('🔍 方法 3: 尝试从 check4d 获取...');
    try {
      const response = await fetch('https://www.check4d.org/', {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
          'Accept': 'text/html'
        }
      });
      
      if (response.ok) {
        const html = await response.text();
        // 简单文本匹配
        const damacaiMatch = html.match(/DAMACAI[\s\S]*?1st[\s\S]*?(\d{4})[\s\S]*?2nd[\s\S]*?(\d{4})[\s\S]*?3rd[\s\S]*?(\d{4})/i);
        
        if (damacaiMatch) {
          firstPrize = firstPrize || damacaiMatch[1];
          secondPrize = secondPrize || damacaiMatch[2];
          thirdPrize = thirdPrize || damacaiMatch[3];
          console.log(`✅ 从 check4d 获取：1st=${firstPrize}, 2nd=${secondPrize}, 3rd=${thirdPrize}`);
        }
      }
    } catch (err) {
      console.log('⚠️ check4d 获取失败:', err.message);
    }
  }
  
  // 🔍 方法 4: 使用特别奖的第一个号码作为临时替代（仅用于测试）
  if (!firstPrize && apiData.starterList && apiData.starterList.length > 0) {
    console.log('⚠️ 使用特别奖第一个号码作为临时替代');
    // 不推荐，但比显示 ---- 好
  }
  
  console.log('📊 最终获取结果:', { firstPrize, secondPrize, thirdPrize });
  
  return { firstPrize, secondPrize, thirdPrize };
}

function parseDamacaiData(data, drawDate, prizes) {
  const formattedDate = `${drawDate.substring(6,8)}-${drawDate.substring(4,6)}-${drawDate.substring(0,4)}`;
  
  // 🔧 确保始终有值（---- 作为默认）
  const firstPrize = prizes?.firstPrize || "----";
  const secondPrize = prizes?.secondPrize || "----";
  const thirdPrize = prizes?.thirdPrize || "----";
  
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
