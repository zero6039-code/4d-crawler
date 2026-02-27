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
    
    console.log(`📅 获取到 ${drawDates.length} 个开奖日期`);
    console.log(`📅 前 5 个日期：${drawDates.slice(0, 5).join(', ')}`);
    
    if (!drawDates || drawDates.length === 0) {
      throw new Error('没有获取到开奖日期');
    }
    
    // 🔧 获取最近 30 天的日期（约 12 期，因为一周开 3 次）
    const recentDates = drawDates.slice(0, 30);
    console.log(`📅 将获取最近 ${recentDates.length} 期的数据`);
    
    // 🔧 获取所有最近期的数据
    const allResults = [];
    
    for (const drawDate of recentDates) {
      console.log(`\n🔄 处理日期：${drawDate}`);
      
      try {
        const result = await fetchSingleDrawResult(drawDate);
        if (result) {
          allResults.push(result);
        }
      } catch (err) {
        console.log(`⚠️ 日期 ${drawDate} 获取失败：${err.message}`);
      }
    }
    
    // 🔧 保存所有期数的数据
    const outputPath = path.join(__dirname, '../../docs/data/damacai.json');
    const allOutputPath = path.join(__dirname, '../../docs/data/damacai_all.json');
    
    // 最新一期（兼容现有前端）
    fs.writeFileSync(outputPath, JSON.stringify(allResults[0] || defaultData, null, 2));
    
    // 所有历史数据（新前端使用）
    fs.writeFileSync(allOutputPath, JSON.stringify(allResults, null, 2));
    
    console.log(`\n✅ 共获取 ${allResults.length} 期数据`);
    console.log('📄 最新数据文件:', outputPath);
    console.log('📄 历史数据文件:', allOutputPath);
    console.log('📊 最新数据:', JSON.stringify(allResults[0], null, 2));
    
    return allResults[0] || defaultData;
    
  } catch (error) {
    console.error(`❌ 获取失败：${error.message}`);
    return defaultData;
  }
}

// 🔧 获取单期开奖结果
async function fetchSingleDrawResult(drawDate) {
  try {
    console.log(`  📅 获取 ${drawDate} 的数据...`);
    
    // 步骤 1: 获取结果文件链接
    const linkResponse = await fetch(`https://www.damacai.com.my/callpassresult?pastdate=${drawDate}`, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'cookiesession': '363'
      }
    });
    
    if (!linkResponse.ok) {
      console.log(`  ⚠️ 获取链接失败：HTTP ${linkResponse.status}`);
      return null;
    }
    
    const linkData = await linkResponse.json();
    const resultUrl = linkData.link;
    
    if (!resultUrl) {
      console.log(`  ⚠️ 没有结果链接`);
      return null;
    }
    
    // 步骤 2: 获取 API 数据（特别奖/安慰奖）
    const resultResponse = await fetch(resultUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
      }
    });
    
    if (!resultResponse.ok) {
      console.log(`  ⚠️ 获取数据失败：HTTP ${resultResponse.status}`);
      return null;
    }
    
    const resultData = await resultResponse.json();
    console.log(`  ✅ API 数据获取成功`);
    
    // 步骤 3: 获取 1st/2nd/3rd 号码
    const prizes = await fetchPrizesFromMultipleSources(drawDate, resultData);
    
    return parseDamacaiData(resultData, drawDate, prizes);
    
  } catch (error) {
    console.log(`  ❌ 错误：${error.message}`);
    return null;
  }
}

// 🔧 从多个数据源获取 1st/2nd/3rd 号码
async function fetchPrizesFromMultipleSources(drawDate, apiData) {
  let firstPrize = null;
  let secondPrize = null;
  let thirdPrize = null;
  
  const formattedDate = `${drawDate.substring(6,8)}-${drawDate.substring(4,6)}-${drawDate.substring(0,4)}`;
  
  // 🔍 方法 1: 从 4d4d.co 获取（主要数据源）
  console.log(`  🔍 从 4d4d.co 获取 ${formattedDate} 的数据...`);
  try {
    const response = await fetch('https://4d4d.co/', {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html'
      }
    });
    
    if (response.ok) {
      const html = await response.text();
      const dom = new JSDOM(html);
      const doc = dom.window.document;
      
      // 查找所有 DAMACAI 结果区域
      const damacaiSections = doc.querySelectorAll('table, .company-result, [data-company="damacai"]');
      
      for (const section of damacaiSections) {
        const text = section.textContent || '';
        
        // 检查是否包含当前日期
        if (!text.includes(formattedDate) && !text.includes(drawDate)) {
          continue;
        }
        
        // 查找 1st/2nd/3rd
        const rows = section.querySelectorAll('tr, .prize-row, .result-row');
        
        for (const row of rows) {
          const rowText = row.textContent?.toLowerCase() || '';
          const numberMatch = row.textContent?.match(/\d{4}/);
          
          if (!numberMatch) continue;
          
          const number = numberMatch[0];
          
          if (!firstPrize && (rowText.includes('1st') || rowText.includes('first') || rowText.includes('首奖'))) {
            firstPrize = number;
            console.log(`    ✅ 找到 1st Prize: ${number}`);
          } else if (!secondPrize && (rowText.includes('2nd') || rowText.includes('second') || rowText.includes('二奖'))) {
            secondPrize = number;
            console.log(`    ✅ 找到 2nd Prize: ${number}`);
          } else if (!thirdPrize && (rowText.includes('3rd') || rowText.includes('third') || rowText.includes('三奖'))) {
            thirdPrize = number;
            console.log(`    ✅ 找到 3rd Prize: ${number}`);
          }
        }
      }
    }
  } catch (err) {
    console.log(`  ⚠️ 4d4d.co 获取失败：${err.message}`);
  }
  
  // 🔍 方法 2: 从 live4d2u 获取（备用）
  if (!firstPrize || !secondPrize || !thirdPrize) {
    console.log(`  🔍 从 live4d2u 获取...`);
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
        
        const damacaiSection = doc.querySelector('[data-company="damacai"], .damacai');
        
        if (damacaiSection) {
          const prizeElements = damacaiSection.querySelectorAll('[class*="prize"], [class*="Prize"]');
          let index = 0;
          
          for (const el of prizeElements) {
            const text = el.textContent?.trim();
            if (/^\d{4}$/.test(text)) {
              if (index === 0 && !firstPrize) firstPrize = text;
              else if (index === 1 && !secondPrize) secondPrize = text;
              else if (index === 2 && !thirdPrize) thirdPrize = text;
              index++;
            }
          }
          
          if (firstPrize) {
            console.log(`    ✅ 从 live4d2u 获取：1st=${firstPrize}, 2nd=${secondPrize}, 3rd=${thirdPrize}`);
          }
        }
      }
    } catch (err) {
      console.log(`  ⚠️ live4d2u 获取失败：${err.message}`);
    }
  }
  
  console.log(`  📊 获取结果：{ firstPrize: ${firstPrize}, secondPrize: ${secondPrize}, thirdPrize: ${thirdPrize} }`);
  
  return { firstPrize, secondPrize, thirdPrize };
}

function parseDamacaiData(data, drawDate, prizes) {
  const formattedDate = `${drawDate.substring(6,8)}-${drawDate.substring(4,6)}-${drawDate.substring(0,4)}`;
  
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
}

main();
