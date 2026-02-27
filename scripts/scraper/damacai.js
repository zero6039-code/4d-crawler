const fetch = require('node-fetch');
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

// ==================== 配置 ====================
const CONFIG = {
    outputPath: path.join(__dirname, '../../docs/data/damacai.json'),
    timeout: 10000,
    retries: 3,
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
};

// ==================== 工具函数 ====================
function log(message, type = 'info') {
    const timestamp = new Date().toLocaleString('en-GB');
    const prefix = type === 'error' ? '❌' : type === 'success' ? '✅' : '🔄';
    console.log(`${prefix} [${timestamp}] ${message}`);
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function fetchWithRetry(url, options = {}, retries = CONFIG.retries) {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'User-Agent': CONFIG.userAgent,
                    ...(options.headers || {})
                },
                timeout: CONFIG.timeout
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.text();
        } catch (error) {
            log(`请求失败 (尝试 ${i + 1}/${retries}): ${error.message}`, 'error');
            if (i === retries - 1) throw error;
            await sleep(2000 * (i + 1)); // 指数退避
        }
    }
}

// ==================== 日期处理 ====================
function getLatestDrawDate() {
    const now = new Date();
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const dayName = days[now.getDay()];
    
    // DAMACAI 开奖日：周三、周六、周日
    const drawDays = ['Wed', 'Sat', 'Sun'];
    
    let drawDate = new Date(now);
    
    // 如果今天不是开奖日，找最近的一个开奖日
    if (!drawDays.includes(dayName)) {
        let daysBack = 0;
        while (!drawDays.includes(days[drawDate.getDay()]) && daysBack < 7) {
            drawDate.setDate(drawDate.getDate() - 1);
            daysBack++;
        }
    }
    
    const day = String(drawDate.getDate()).padStart(2, '0');
    const month = String(drawDate.getMonth() + 1).padStart(2, '0');
    const year = drawDate.getFullYear();
    const dayStr = days[drawDate.getDay()];
    
    return {
        display: `${day}-${month}-${year} (${dayStr})`,
        iso: `${year}-${month}-${day}`,
        drawNo: generateDrawNumber(drawDate)
    };
}

function generateDrawNumber(date) {
    // 生成期号（示例格式：6042-26）
    // 实际需要根据 DAMACAI 的规则调整
    const year = date.getFullYear() % 100;
    const month = date.getMonth() + 1;
    const day = date.getDate();
    
    // 这里使用一个示例期号，实际需要从官网获取
    const baseNumber = 6000 + Math.floor((month * 100 + day) / 2);
    return `${baseNumber}-${year}`;
}

// ==================== 数据解析 ====================
function parseDamacaiResults(html) {
    try {
        const dom = new JSDOM(html);
        const doc = dom.window.document;
        
        const results = {
            '1st': '',
            '2nd': '',
            '3rd': '',
            special: [],
            consolation: []
        };
        
        // 方案 1: 查找包含 prize 或 number 的元素
        const allElements = doc.querySelectorAll('*');
        
        for (let el of allElements) {
            const text = el.textContent?.trim() || '';
            
            // 匹配 4D 号码（4位数字）
            if (/^\d{4}$/.test(text)) {
                const parent = el.parentElement;
                const parentText = parent?.textContent?.toLowerCase() || '';
                
                // 判断奖项类型
                if (parentText.includes('1st') || parentText.includes('first')) {
                    results['1st'] = text;
                } else if (parentText.includes('2nd') || parentText.includes('second')) {
                    results['2nd'] = text;
                } else if (parentText.includes('3rd') || parentText.includes('third')) {
                    results['3rd'] = text;
                }
            }
        }
        
        // 方案 2: 尝试查找 special 和 consolation
        const specialSection = doc.querySelector('[class*="special"], [class*="Special"]');
        const consolationSection = doc.querySelector('[class*="consolation"], [class*="Consolation"]');
        
        if (specialSection) {
            const numbers = specialSection.textContent?.match(/\d{4}/g) || [];
            results.special = numbers.slice(0, 10);
        }
        
        if (consolationSection) {
            const numbers = consolationSection.textContent?.match(/\d{4}/g) || [];
            results.consolation = numbers.slice(0, 10);
        }
        
        return results;
    } catch (error) {
        log(`解析 HTML 失败: ${error.message}`, 'error');
        return null;
    }
}

// ==================== API 抓取方案 ====================
async function fetchFromAPI() {
    log('尝试从 API 获取数据...');
    
    // DAMACAI 可能的 API 端点（需要根据实际情况调整）
    const apiEndpoints = [
        'https://www.damacai.com.my/api/results/latest',
        'https://www.damacai.com.my/results.json',
        'https://api.damacai.com.my/v1/results'
    ];
    
    for (const endpoint of apiEndpoints) {
        try {
            const response = await fetch(endpoint, {
                headers: {
                    'User-Agent': CONFIG.userAgent,
                    'Accept': 'application/json'
                },
                timeout: CONFIG.timeout
            });
            
            if (response.ok) {
                const data = await response.json();
                log(`✅ API 成功: ${endpoint}`);
                return data;
            }
        } catch (error) {
            log(`API 失败: ${endpoint} - ${error.message}`, 'error');
        }
    }
    
    return null;
}

// ==================== 网页抓取方案 ====================
async function fetchFromWebsite() {
    log('尝试从官网网页获取数据...');
    
    const urls = [
        'https://www.damacai.com.my/en-us/game/4d/results',
        'https://www.damacai.com.my/results/4d'
    ];
    
    for (const url of urls) {
        try {
            const html = await fetchWithRetry(url);
            const results = parseDamacaiResults(html);
            
            if (results && (results['1st'] || results.special.length > 0)) {
                log(`✅ 网页抓取成功: ${url}`);
                return results;
            }
        } catch (error) {
            log(`网页抓取失败: ${url} - ${error.message}`, 'error');
        }
    }
    
    return null;
}

// ==================== 生成完整数据 ====================
function buildCompleteData(results) {
    const dateInfo = getLatestDrawDate();
    
    return {
        draw_date: dateInfo.display,
        global_draw_no: dateInfo.drawNo,
        '1st': results['1st'] || '----',
        '2nd': results['2nd'] || '----',
        '3rd': results['3rd'] || '----',
        special: results.special.length > 0 
            ? results.special 
            : Array(10).fill('----'),
        consolation: results.consolation.length > 0 
            ? results.consolation 
            : Array(10).fill('----'),
        draw_info: `${dateInfo.display} #${dateInfo.drawNo}`
    };
}

// ==================== 保存数据 ====================
function saveData(data) {
    try {
        // 确保目录存在
        const dir = path.dirname(CONFIG.outputPath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
        
        // 写入文件
        fs.writeFileSync(CONFIG.outputPath, JSON.stringify(data, null, 2), 'utf8');
        log(`✅ 数据已保存: ${CONFIG.outputPath}`, 'success');
        log(`📊 首奖: ${data['1st']}`);
        log(`📊 二奖: ${data['2nd']}`);
        log(`📊 三奖: ${data['3rd']}`);
    } catch (error) {
        log(`保存数据失败: ${error.message}`, 'error');
        throw error;
    }
}

// ==================== 主函数 ====================
async function main() {
    log('开始抓取 DAMACAI 数据...');
    
    try {
        let results = null;
        
        // 方案 1: 尝试 API
        results = await fetchFromAPI();
        
        // 方案 2: 尝试网页抓取
        if (!results) {
            results = await fetchFromWebsite();
        }
        
        // 方案 3: 如果都失败，使用占位数据
        if (!results) {
            log('⚠️  所有抓取方案失败，使用占位数据', 'error');
            results = {
                '1st': '',
                '2nd': '',
                '3rd': '',
                special: [],
                consolation: []
            };
        }
        
        // 构建完整数据
        const completeData = buildCompleteData(results);
        
        // 保存数据
        saveData(completeData);
        
        log('🎉 DAMACAI 数据更新完成！', 'success');
        
    } catch (error) {
        log(`程序执行失败: ${error.message}`, 'error');
        process.exit(1);
    }
}

// 运行主函数
main();
