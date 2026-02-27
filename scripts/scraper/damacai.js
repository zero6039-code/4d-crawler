// scripts/scraper/damacai.js
const fetch = require('node-fetch');
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
    console.log('✅ 数据获取成功');
    console.log('📊 原始数据:', JSON.stringify(resultData, null, 2));
    
    return parseDamacaiData(resultData, latestDate);
    
  } catch (error) {
    console.error(`❌ 获取失败：${error.message}`);
    return defaultData;
  }
}

function parseDamacaiData(data, drawDate) {
  const formattedDate = `${drawDate.substring(6,8)}-${drawDate.substring(4,6)}-${drawDate.substring(0,4)}`;
  
  // 🔧 关键修复：使用正确的字段名称
  // 头奖、二奖、三奖
  const firstPrize = data.p1HorseNo || data.FirstPrize || data.firstPrize || "----";
  const secondPrize = data.p2HorseNo || data.SecondPrize || data.secondPrize || "----";
  const thirdPrize = data.p3HorseNo || data.ThirdPrize || data.thirdPrize || "----";
  
  // 特别奖 (starterList)
  let special = data.starterList || data.starterHorseList || data.Special || data.special || [];
  if (!Array.isArray(special)) special = [];
  
  // 安慰奖 (consolidateList)
  let consolation = data.consolidateList || data.Consolation || data.consolation || [];
  if (!Array.isArray(consolation)) consolation = [];
  
  // 🔧 过滤掉 "-" 并填充到 10 个
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
