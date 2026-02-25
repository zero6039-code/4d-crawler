const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');

// 目标网站列表（请替换为真实 URL）
const SOURCES = {
  damacai: 'https://livedraw.damacai.com.my/',
  magnum: 'https://www.magnum4d.my/',
  // 添加其他公司...
};

// 通用的请求头，模拟浏览器
const headers = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
};

async function fetchCompany(url, companyKey) {
  try {
    console.log(`正在抓取 ${companyKey}...`);
    const response = await axios.get(url, { headers, timeout: 10000 });
    const $ = cheerio.load(response.data);

    // 根据实际网页结构调整选择器
    // 示例：假设每个公司页面结构相似
    const first = $('.prize-first .number').text().trim() || '';
    const second = $('.prize-second .number').text().trim() || '';
    const third = $('.prize-third .number').text().trim() || '';

    // 特别奖和安慰奖（通常为列表）
    const special = [];
    $('.special-list .item').each((i, el) => {
      special.push($(el).text().trim());
    });

    const consolation = [];
    $('.consolation-list .item').each((i, el) => {
      consolation.push($(el).text().trim());
    });

    // 开奖信息（如日期、期号）
    const drawInfo = $('.draw-info').text().trim() || '';

    console.log(`${companyKey} 抓取成功：1st=${first}, 2nd=${second}, 3rd=${third}, special数量=${special.length}`);

    return {
      '1st': first,
      '2nd': second,
      '3rd': third,
      special,
      consolation,
      draw_info: drawInfo
    };
  } catch (err) {
    console.error(`抓取 ${companyKey} 失败:`, err.message);
    // 返回空数据，避免整体失败
    return {
      '1st': '',
      '2nd': '',
      '3rd': '',
      special: [],
      consolation: [],
      draw_info: ''
    };
  }
}

async function fetchAll() {
  console.log('开始抓取所有公司...');
  const results = {};

  for (const [key, url] of Object.entries(SOURCES)) {
    results[key] = await fetchCompany(url, key);
    // 可适当增加延时，避免请求过快
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  // 构造最终输出
  const output = {
    draw_date: new Date().toLocaleString('en-GB', {
      weekday: 'short',
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    }).replace(/\//g, '/'),  // 例如 "Wed, 25/02/2026"
    global_draw_no: '需从某处获取或留空',
    results
  };

  // 写入文件
  fs.writeFileSync('docs/data.json', JSON.stringify(output, null, 2));
  console.log('数据已写入 docs/data.json');
}

fetchAll().catch(err => {
  console.error('脚本执行出错:', err);
  process.exit(1);
});
