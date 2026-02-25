const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');

// 目标网站列表（示例，请替换为真实 URL）
const SOURCES = {
  damacai: 'https://livedraw.damacai.com.my/',
  magnum: 'https://www.magnum4d.my/',
  // ... 其他公司
};

async function fetchDamacai() {
  const { data } = await axios.get(SOURCES.damacai);
  const $ = cheerio.load(data);
  // 根据实际 DOM 提取数据
  return {
    '1st': $('.first-prize').text().trim(),
    '2nd': $('.second-prize').text().trim(),
    '3rd': $('.third-prize').text().trim(),
    special: [],
    consolation: [],
    draw_info: $('.draw-info').text().trim()
  };
}

async function fetchAll() {
  const results = {};
  // 并行抓取所有公司
  await Promise.all(
    Object.keys(SOURCES).map(async (key) => {
      try {
        results[key] = await fetchDamacai(); // 需要为每个公司写对应的解析函数
      } catch (err) {
        console.error(`抓取 ${key} 失败:`, err.message);
        results[key] = {}; // 留空避免整体失败
      }
    })
  );

  const output = {
    draw_date: new Date().toLocaleString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric', weekday: 'short' }),
    global_draw_no: '自动生成或从某处获取',
    results
  };

  fs.writeFileSync('docs/data.json', JSON.stringify(output, null, 2));
  console.log('数据已更新');
}

fetchAll();
