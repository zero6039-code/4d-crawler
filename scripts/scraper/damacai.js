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
    
    // 步骤 1: 获取开奖日期
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
    
    // 🔧 关键修复：按日期降序排序（最新的在前面）
    drawDates = drawDates.sort((a, b) => b.localeCompare(a));
    
    console.log(`📅 所有开奖日期: ${drawDates.slice(0, 5).join(', ')}...`);
    
    if (!drawDates || drawDates.length === 0) {
      throw new Error('没有获取到开奖日期');
    }
    
    // 获取最新开奖日期 (YYYYMMDD 格式)
    const latestDate = drawDates[0];
    console.log(`📅 最新开奖日期：${latestDate}`);
    
    // 步骤 2: 获取结果文件链接
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
    
    console.log(`🔗 结果链接：${resultUrl.substring(0, 50)}...`);
    
    // 步骤 3: 获取实际开奖数据
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
  // 格式化日期：YYYYMMDD → DD-MM-YYYY
  const formattedDate = `${drawDate.substring(6,8)}-${drawDate.substring(4,6)}-${drawDate.substring(0,4)}`;
  
  // 🔧 关键修复：确保字段名称匹配（大小写敏感）
  return {
    draw_date: formattedDate,
    global_draw_no: data.DrawNo || data.drawNo || "----",
    "1st": data.FirstPrize || data.firstPrize || "----",
    "2nd": data.SecondPrize || data.secondPrize || "----",
    "3rd": data.ThirdPrize || data.thirdPrize || "----",
    special: data.Special || data.special || Array(10).fill("----"),
    consolation: data.Consolation || data.consolation || Array(10).fill("----"),
    draw_info: (data.DrawNo || data.drawNo) 
      ? `${formattedDate} #${data.DrawNo || data.drawNo}`
      : "----"
  };
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
