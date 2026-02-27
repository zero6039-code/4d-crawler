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
    console.log('🔄 尝试从 DAMACAI 官网获取数据...');
    
    // 方法 1: 尝试官方 JSON 端点
    const apiUrl = 'https://www.damacai.com.my/ListPastResult';
    const response = await fetch(apiUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.damacai.com.my/'
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ 从 API 获取成功');
      return parseDamacaiData(data);
    }
    
    // 方法 2: 爬虫官网页面
    console.log('🔄 API 不可用，尝试爬虫官网页面...');
    const pageUrl = 'https://www.damacai.com.my/past-draw-result';
    const pageResponse = await fetch(pageUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html',
        'Referer': 'https://www.damacai.com.my/'
      }
    });
    
    if (!pageResponse.ok) {
      throw new Error(`HTTP ${pageResponse.status}: ${pageResponse.statusText}`);
    }
    
    const html = await pageResponse.text();
    return parseDamacaiHTML(html);
    
  } catch (error) {
    console.error(`❌ 获取失败: ${error.message}`);
    return defaultData;
  }
}

function parseDamacaiData(data) {
  // 根据实际 API 返回格式解析
  return {
    draw_date: data.drawDate || "----",
    global_draw_no: data.drawNumber || "----",
    "1st": data.firstPrize || "----",
    "2nd": data.secondPrize || "----",
    "3rd": data.thirdPrize || "----",
    special: data.specialPrizes || Array(10).fill("----"),
    consolation: data.consolationPrizes || Array(10).fill("----"),
    draw_info: data.drawDate && data.drawNumber 
      ? `(${data.day}) ${data.drawDate} #${data.drawNumber}`
      : "----"
  };
}

function parseDamacaiHTML(html) {
  const dom = new JSDOM(html);
  const doc = dom.window.document;
  
  // 根据实际网页结构调整选择器
  const result = { ...defaultData };
  
  // 示例：需要根据实际 HTML 调整
  const drawNo = doc.querySelector('.draw-number')?.textContent;
  const firstPrize = doc.querySelector('.prize-1st')?.textContent;
  
  if (drawNo) result.global_draw_no = drawNo.trim();
  if (firstPrize) result["1st"] = firstPrize.trim();
  
  result.draw_info = result.global_draw_no !== "----" 
    ? `Latest Draw #${result.global_draw_no}` 
    : "----";
  
  return result;
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
