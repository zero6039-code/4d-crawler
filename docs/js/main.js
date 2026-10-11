/* docs/js/main.js */

// ==================== 全局弹窗与模式控制 ====================
function openModal(id) { var el = document.getElementById(id); if (el) el.style.display = 'flex'; }
function closeModal(id) { var el = document.getElementById(id); if (el) el.style.display = 'none'; }

function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    var isDark = document.body.classList.contains('dark-mode');
    var btn = document.getElementById('dark-mode-btn');
    if (btn) {
        btn.innerHTML = isDark 
            ? '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>'
            : '<svg viewBox="0 0 24 24"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>';
        localStorage.setItem('darkMode', isDark ? 'enabled' : 'disabled');
    }
}

// ==================== 注入全局悬停效果与专属布局样式 ====================
const totoStyles = `
    /* ==== 1. 顶部第一、二、三奖的悬停效果 ==== */
    .prize-card { transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); cursor: default; }
    .prize-card:hover { 
        transform: translateY(-3px); 
        box-shadow: 0 8px 20px rgba(0,0,0,0.1); 
        background: rgba(255,255,255,0.95) !important; 
    }
    .prize-card .number { transition: transform 0.25s ease; }
    .prize-card:hover .number { transform: scale(1.08); }
    body.dark-mode .prize-card:hover { 
        background: rgba(30,41,59,0.95) !important; 
        box-shadow: 0 8px 20px rgba(0,0,0,0.5); 
    }
    body.dark-mode .prize-card:hover .number { text-shadow: 0 0 15px rgba(251,191,36,0.5); }

    /* ==== 2. 其他所有号码的通用悬停效果 ==== */
    .number-item { transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); cursor: default; }
    .number-item:hover { 
        transform: translateY(-3px) scale(1.08); 
        box-shadow: 0 6px 15px rgba(0,0,0,0.1); 
        background: #ffffff !important; 
        border-color: #cbd5e1 !important; 
        z-index: 10; 
    }
    body.dark-mode .number-item:hover { 
        background: rgba(30,41,59,0.95) !important; 
        border-color: rgba(255,255,255,0.2) !important; 
        box-shadow: 0 6px 15px rgba(0,0,0,0.5); 
        color: #fbbf24 !important; 
    }

    /* ==== 3. 5D 专属布局 ==== */
    .toto-5d-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 8px; }
    .toto-5d-box { 
        background: rgba(255,255,255,0.8); border-radius: 16px; padding: 12px 8px; text-align: center; 
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); cursor: default; 
        box-shadow: 0 2px 8px rgba(0,0,0,0.03); border: 1px solid rgba(255,255,255,0.5);
    }
    .toto-5d-box:hover { transform: translateY(-3px); box-shadow: 0 8px 16px rgba(0,0,0,0.1); background: #fff; }
    .toto-5d-box .label { font-size: 0.85rem; color: #5f6b7a; font-weight: 600; text-transform: uppercase; }
    .toto-5d-box .num { font-size: 1.8rem; font-weight: 800; color: #c62828; font-family: 'Courier New', monospace; margin-top: 4px; line-height: 1.2; }
    body.dark-mode .toto-5d-box { background: rgba(15,23,42,0.8); border-color: rgba(255,255,255,0.05); }
    body.dark-mode .toto-5d-box:hover { background: rgba(30,41,59,0.9); box-shadow: 0 8px 16px rgba(0,0,0,0.4); }
    body.dark-mode .toto-5d-box .label { color: #94a3b8; }
    body.dark-mode .toto-5d-box .num { color: #fbbf24; text-shadow: 0 0 15px rgba(251,191,36,0.3); }
    
    /* ==== 4. 6D 专属布局 ==== */
    .toto-6d-grid { display: grid; grid-template-columns: 1fr; gap: 8px; margin-top: 8px; }
    .toto-6d-row { 
        display: flex; align-items: center; justify-content: space-between; background: rgba(255,255,255,0.8); 
        border-radius: 12px; padding: 10px 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.03); 
        flex-wrap: wrap; gap: 6px; transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); 
        cursor: default; border: 1px solid rgba(255,255,255,0.5);
    }
    .toto-6d-row:hover { transform: translateX(4px); box-shadow: 0 6px 15px rgba(0,0,0,0.08); background: #fff; }
    .toto-6d-row .label { font-size: 0.9rem; color: #5f6b7a; font-weight: 600; width: 42px; }
    .toto-6d-row .main-num { font-size: 1.4rem; font-weight: 800; color: #c62828; font-family: 'Courier New', monospace; }
    .toto-6d-row .alt-num { font-size: 1.4rem; font-weight: 800; color: #c62828; font-family: 'Courier New', monospace; }
    .toto-6d-row .or-text { font-size: 0.85rem; color: #94a3b8; margin: 0 6px; font-weight: 500; }
    body.dark-mode .toto-6d-row { background: rgba(15,23,42,0.8); border-color: rgba(255,255,255,0.05); }
    body.dark-mode .toto-6d-row:hover { background: rgba(30,41,59,0.9); box-shadow: 0 6px 15px rgba(0,0,0,0.4); }
    body.dark-mode .toto-6d-row .label { color: #94a3b8; }
    body.dark-mode .toto-6d-row .main-num, body.dark-mode .toto-6d-row .alt-num { color: #fbbf24; text-shadow: 0 0 10px rgba(251,191,36,0.3); }

    /* ==== 5. Singapore Toto 专属布局 ==== */
    .toto-ball-row { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; margin-top: 10px; }
    .toto-ball { 
        width: 44px; height: 44px; border-radius: 50%; background: #ffffff; border: 1px solid #cbd5e1; 
        display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.2rem; 
        color: #c62828; box-shadow: 0 2px 5px rgba(0,0,0,0.05); transition: all 0.2s; cursor: default;
    }
    .toto-ball:hover { transform: translateY(-3px) scale(1.05); box-shadow: 0 5px 12px rgba(0,0,0,0.15); }
    .toto-special-ball { 
        width: 44px; height: 44px; border-radius: 50%; background: #c62828; color: #ffffff; 
        display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.2rem; 
        box-shadow: 0 2px 5px rgba(198,40,40,0.3); transition: all 0.2s; cursor: default;
    }
    .toto-special-ball:hover { transform: translateY(-3px) scale(1.05); box-shadow: 0 5px 12px rgba(198,40,40,0.5); }
    
    .singapore-toto-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; margin-top: 12px; border-radius: 12px; overflow: hidden; }
    .singapore-toto-table th { background: #4a5568; color: white; padding: 8px 4px; text-align: center; font-weight: 600; font-size: 0.8rem; }
    .singapore-toto-table td { padding: 8px 4px; text-align: center; border-bottom: 1px solid #e2e8f0; background: rgba(255,255,255,0.8); }
    .singapore-toto-table tr:last-child td { border-bottom: none; }
    body.dark-mode .toto-ball { background: #1a202c; border-color: #4a5568; color: #fbbf24; }
    body.dark-mode .toto-special-ball { background: #9b2c2c; color: #fbbf24; }
    body.dark-mode .singapore-toto-table th { background: #2d3748; }
    body.dark-mode .singapore-toto-table td { background: rgba(15,23,42,0.8); border-bottom-color: #4a5568; color: #e2e8f0; }
`;
const styleSheet = document.createElement("style");
styleSheet.textContent = totoStyles;
document.head.appendChild(styleSheet);

// ==================== 常量定义 ====================
const COMPANY_LIST = [
    'damacai', 'magnum', 'toto', 'singapore', 
    'grand_dragon', 'perdana4d', 'lucky_hari', 
    'sandakan', 'sarawak_cashsweep', 
    'sabah', 'damacai_1p3d', 
    'sabah_lotto', 'singapore_toto', 'sportstoto_lotto',
    'magnum_jackpot_gold', 'sportstoto_5d', 'sportstoto_6d',
    'magnum_life', 'sportstoto_fireball'
];

const NAME_MAP = {
    'grand_dragon': 'GRAND DRAGON 豪龙', 'damacai': 'DAMACAI 4D', 'magnum': 'MAGNUM 4D',
    'toto': 'TOTO 4D', 'singapore': 'SINGAPORE 4D', 'damacai_1p3d': 'DAMACAI 1+3D',
    'sandakan': 'SANDAKAN 4D', 'sarawak_cashsweep': 'SARAWAK CASHSWEEP', 'sabah': 'SABAH 88 4D',
    'sabah_lotto': 'SABAH LOTTO', 'singapore_toto': 'SINGAPORE TOTO', 'sportstoto_lotto': 'SPORTS TOTO LOTTO',
    'magnum_jackpot_gold': 'MAGNUM JACKPOT GOLD', 'sportstoto_5d': 'SPORTS TOTO 5D',
    'sportstoto_6d': 'SPORTS TOTO 6D', 'magnum_life': 'MAGNUM LIFE', 'sportstoto_fireball': 'SPORTS TOTO FIREBALL',
    'perdana4d': 'PERDANA LOTTERY 4D',
    'lucky_hari': 'LUCKY HARIHARI 天天好运'
};

const SPECIAL_COMPANIES = ['sportstoto_fireball', 'singapore_toto', 'magnum_jackpot_gold', 'sportstoto_5d', 'sportstoto_6d', 'magnum_life', 'sportstoto_lotto', 'sabah_lotto'];
const HIDDEN_COMPANIES = ['sportstoto_fireball'];

const COMPANY_IMAGE_MAP = {
    'damacai': 'damacai.png', 'damacai_1p3d': 'damacai1+3.png', 'sandakan': 'sandakan_logo.png',
    'sarawak_cashsweep': 'sarawak.png', 'sabah': 'sabah88.png', 'sabah_lotto': 'sabahlotto.png',
    'grand_dragon': 'granddragon.png', 'magnum': 'magnum.png', 'toto': 'toto.png',
    'singapore': 'singapore4d.png', 'singapore_toto': 'singapore-pools.png',
    'perdana4d': 'Perdana4D.png',
    'lucky_hari': 'luckly_hari.png'
};

// ==================== 全局状态 ====================
let availableDates = [], availableDatesSet = new Set(), selectedDate = null, currentCalendarDate = new Date(), isFallbackMode = false;

// ==================== 日期工具函数 ====================
const ymdToDmy = ymd => { if(!ymd) return ''; let p = ymd.split('-'); return p.length===3 ? `${p[2]}-${p[1]}-${p[0]}` : ymd; };
const parseDMY = str => { let p = str.split('-'); let d,m,y; if(p[0].length===4){[y,m,d]=p.map(Number);}else{[d,m,y]=p.map(Number);} return {year:y,month:m,day:d}; };
const toSortKey = str => { let {year,month,day} = parseDMY(str); return year*10000+month*100+day; };
const sortDatesDesc = dates => dates.sort((a,b)=>toSortKey(b)-toSortKey(a));
const formatDisplayDate = str => { if(!str) return '加载中...'; let dmy = ymdToDmy(str); let p = dmy.split('-'); let d = new Date(p[2],p[1]-1,p[0]); return `${dmy} ${d.toLocaleDateString('en-US',{weekday:'short'})}`; };

// ==================== 下拉框与外部点击 ====================
window.toggleDateDropdown = function() { document.getElementById('date-dropdown').classList.toggle('show'); };

document.addEventListener('click', e => {
    const dropdown = document.getElementById('date-dropdown');
    if (!dropdown.contains(e.target)) dropdown.classList.remove('show');
    const popup = document.getElementById('calendar-popup'), btn = document.getElementById('calendar-btn');
    if (!popup.contains(e.target) && e.target !== btn) popup.style.display = 'none';
});

// ==================== 数据加载与 UI 更新 ====================
async function loadDateIndex() {
    try {
        const res = await fetch(`data/dates.json?t=${Date.now()}`, { cache: 'no-store' });
        if (res.ok) {
            let dates = await res.json();
            availableDates = sortDatesDesc(dates);
            availableDatesSet = new Set(availableDates);
            selectedDate = availableDates.length > 0 ? availableDates[0] : null;
        } else { document.getElementById('date-dropdown-content').innerHTML = '<div style="text-align:center;padding:20px;">暂无历史数据</div>'; }
    } catch (e) { document.getElementById('date-dropdown-content').innerHTML = '<div style="text-align:center;padding:20px;">加载失败</div>'; }
    
    renderDateDropdown(); updateDateBtnWithLatest();
    if (selectedDate) await fetchAndRenderData(selectedDate);
    else { document.getElementById('companies-grid').innerHTML = '<p style="text-align:center;color:#666;">暂无数据</p>'; }
}

function renderDateDropdown() {
    const container = document.getElementById('date-dropdown-content');
    if (!availableDates || availableDates.length === 0) return;
    container.innerHTML = availableDates.map(date => `<div class="date-option ${date===selectedDate?'active':''}" onclick="selectDate('${date}')">${formatDisplayDate(date)}</div>`).join('');
}

window.selectDate = date => { 
    selectedDate = date; isFallbackMode = false; 
    document.getElementById('fallback-banner').style.display = 'none'; 
    renderDateDropdown(); updateDateBtnWithLatest(); 
    document.getElementById('date-dropdown').classList.remove('show'); 
    fetchAndRenderData(date); 
};

function updateDateBtnWithLatest() { document.getElementById('selected-date').innerText = selectedDate ? formatDisplayDate(selectedDate) : '选择日期'; }

window.forceRefresh = () => { 
    if (selectedDate) { 
        isFallbackMode = false; 
        document.getElementById('fallback-banner').style.display = 'none'; 
        fetchAndRenderData(selectedDate, true); 
    } 
};

function updateStatus(type, text, updateTime = null) { 
    const span = document.getElementById('status-text'); 
    const ind = span.querySelector('.status-indicator'); 
    ind.className = `status-indicator ${type}`; 
    span.innerHTML = `${ind.outerHTML}${text}`; 
    if (updateTime) document.getElementById('update-time').innerText = updateTime; 
}

// ==================== 核心数据抓取与部分渲染 ====================
async function fetchAndRenderData(dateStr, isRefresh = false) {
    const grid = document.getElementById('companies-grid');
    grid.innerHTML = '<p style="text-align:center;grid-column:1/-1;color:#666;">🔄 正在加载数据...</p>';
    updateStatus('loading', '正在加载...');
    const isLatest = availableDates.length > 0 && dateStr === availableDates[0];
    
    const promises = COMPANY_LIST.map(async key => {
        if (HIDDEN_COMPANIES.includes(key)) return { key, data: null };
        const basePath = isLatest ? `data` : `data/${dateStr}`;
        try { const res = await fetch(`${basePath}/${key}.json?t=${Date.now()}`, { cache: 'no-store' }); if (!res.ok) throw new Error(); return { key, data: await res.json() }; } catch { return { key, data: null }; }
    });

    const results = await Promise.all(promises);
    const dataMap = {}; let validCount = 0;
    
    results.forEach(item => {
        if (item.data) {
            let hasData = false;
            
            ['1st', '2nd', '3rd'].forEach(f => {
                if (item.data[f] && typeof item.data[f] === 'string' && item.data[f].trim() !== '') hasData = true;
            });
            
            ['special', 'consolation', 'winning_numbers', 'star', 'power', 'supreme'].forEach(f => {
                if (item.data[f] && Array.isArray(item.data[f]) && item.data[f].some(n => n && n.trim() !== '' && n.trim() !== '****')) hasData = true;
            });

            ['jackpot', 'jackpot1', 'jackpot2'].forEach(f => {
                if (item.data[f] && typeof item.data[f] === 'string' && item.data[f].trim() !== '') hasData = true;
            });

            if (item.data['2nd'] && typeof item.data['2nd'] === 'object' && item.data['2nd'].main) hasData = true;

            if (hasData) { dataMap[item.key] = item.data; validCount++; }
        }
    });

    if (validCount === 0 && !isFallbackMode && availableDates.length > 1) {
        const idx = availableDates.indexOf(dateStr);
        if (idx >= 0 && idx + 1 < availableDates.length) {
            const fallbackDate = availableDates[idx + 1];
            document.getElementById('fallback-banner').innerHTML = `⚠️ <b>${formatDisplayDate(dateStr)}</b> 暂无开奖数据，已自动为您显示 <b>${formatDisplayDate(fallbackDate)}</b> 的最新成绩。`;
            document.getElementById('fallback-banner').style.display = 'block';
            isFallbackMode = true; 
            await fetchAndRenderData(fallbackDate, true); 
            return;
        }
    }
    
    if (validCount === 0) { 
        grid.innerHTML = '<p style="text-align:center;grid-column:1/-1;color:#e53e3e;">❌ 目前暂无任何可用的开奖数据，请稍后再试。</p>'; 
        updateStatus('error', '加载失败'); 
        return; 
    }
    
    renderCompanies(dataMap);
    const now = new Date();
    updateStatus('success', '加载完成', `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')} ${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`);
}

// ==================== 智能渲染公司卡片 ====================
function renderCompanies(dataMap) {
    const grid = document.getElementById('companies-grid'); let html = '';
    COMPANY_LIST.forEach(key => {
        if (HIDDEN_COMPANIES.includes(key)) return; 
        const cd = dataMap[key]; if (!cd) return;
        const name = NAME_MAP[key] || key; 
        const img = COMPANY_IMAGE_MAP[key] ? `images/${COMPANY_IMAGE_MAP[key]}` : null; 
        const isSpecial = SPECIAL_COMPANIES.includes(key);
        
        html += `<div class="company-section" data-company="${key}"><div class="company-title">${name}${img?`<img src="${img}" onerror="this.style.display='none'">`:''}</div><div class="draw-date">${cd.draw_date || '未知'} ${cd.draw_no?'| Draw No: '+cd.draw_no:''}</div><div class="company-content">`;
        
        if (isSpecial) {
            let rendered = false;
            
            // ====== 5D 专属布局 ======
            const is5D = cd.type === '5d' || (!cd.type && cd['6th'] && (!cd['2nd'] || typeof cd['2nd'] === 'string'));
            if (is5D) {
                html += `<div class="subsection"><div class="subsection-title">5D Results</div><div class="toto-5d-grid">`;
                const labels = [['1st', '2nd'], ['3rd', '4th'], ['5th', '6th']];
                labels.forEach(row => {
                    row.forEach(lbl => {
                        if (cd[lbl]) {
                            html += `<div class="toto-5d-box">
                                        <div class="label">${lbl}</div>
                                        <div class="num">${cd[lbl]}</div>
                                     </div>`;
                        }
                    });
                });
                html += `</div></div>`;
                rendered = true;
            }
            
            // ====== 6D 专属布局 ======
            const is6D = cd.type === '6d' || (!cd.type && cd['2nd'] && cd['2nd'].main);
            if (is6D) {
                html += `<div class="subsection"><div class="subsection-title">6D Results</div><div class="toto-6d-grid">`;
                if (cd['1st']) {
                    html += `<div class="toto-6d-row">
                                <span class="label">1st</span>
                                <span class="main-num">${cd['1st']}</span>
                                <span style="flex:1;"></span>
                             </div>`;
                }
                ['2nd','3rd','4th','5th'].forEach(k => {
                    if (cd[k]) {
                        let main = (typeof cd[k] === 'object' && cd[k].main) ? cd[k].main : '----';
                        let alt = (typeof cd[k] === 'object' && cd[k].alt) ? cd[k].alt : '----';
                        if (main === '----' && alt === '----') return;
                        html += `<div class="toto-6d-row">
                                    <span class="label">${k}</span>
                                    <span class="main-num">${main}</span>`;
                        if (alt !== '----') {
                            html += `<span class="or-text">or</span>
                                     <span class="alt-num">${alt}</span>`;
                        }
                        html += `<span style="flex:1;"></span>
                                 </div>`;
                    }
                });
                html += `</div></div>`;
                rendered = true;
            }
            
            // ====== Singapore Toto 专属布局 ======
            if (key === 'singapore_toto') {
                if (cd.winning_numbers && cd.winning_numbers.length > 0) {
                    html += `<div class="subsection"><div class="subsection-title">Winning Numbers</div><div class="toto-ball-row">`;
                    cd.winning_numbers.forEach((num, index) => {
                        if (index === cd.winning_numbers.length - 1) {
                            html += `<div class="toto-special-ball">${num}</div>`;
                        } else {
                            html += `<div class="toto-ball">${num}</div>`;
                        }
                    });
                    html += `</div></div>`;
                }
                if (cd.prize_table && cd.prize_table.length > 0) {
                    html += `<div class="subsection"><div class="subsection-title">Prize Table</div>`;
                    html += `<table class="singapore-toto-table">
                                <thead><tr><th>Prize Group</th><th>Share Amount (Each)</th><th>No. of Winning Shares</th></tr></thead>
                                <tbody>`;
                    cd.prize_table.forEach(row => {
                        html += `<tr>`;
                        row.forEach(cell => html += `<td>${cell}</td>`);
                        html += `</tr>`;
                    });
                    html += `</tbody></table></div>`;
                }
                rendered = true;
            }

            // ====== SPORTS TOTO LOTTO 专属布局 ======
            if (key === 'sportstoto_lotto') {
                const lottoGroups = [
                    { field: 'star', title: 'Star', jpIdx: 0, jpName: 'Jackpot 1' },
                    { field: 'power', title: 'Power', jpIdx: 2, jpName: 'Jackpot' },
                    { field: 'supreme', title: 'Supreme', jpIdx: 3, jpName: 'Jackpot' }
                ];
                lottoGroups.forEach(g => {
                    if (cd[g.field] && Array.isArray(cd[g.field]) && cd[g.field].length > 0) {
                        html += `<div class="subsection"><div class="subsection-title">${g.title}</div><div class="number-list">`;
                        cd[g.field].forEach(n => html += `<span class="number-item">${n}</span>`);
                        html += `</div>`;
                        if (cd.jackpots && cd.jackpots[g.jpIdx] && cd.jackpots[g.jpIdx].trim() !== '') {
                            html += `<div style="margin-top: 8px; font-weight: 700; color: #d97706; font-size: 1rem;">${g.jpName}: ${cd.jackpots[g.jpIdx]}</div>`;
                        }
                        html += `</div>`;
                        rendered = true;
                    }
                });
            }

            // ====== SABAH LOTTO 专属布局 (拆分为3个卡片) ======
            if (key === 'sabah_lotto') {
                let card1Html = '', card2Html = '', card3Html = '';
                const sharedDate = `<div class="draw-date">${cd.draw_date || '未知'} ${cd.draw_no?'| Draw No: '+cd.draw_no:''}</div>`;
                const sharedImg = img ? `<img src="${img}" onerror="this.style.display='none'">` : '';

                // 卡片1：主卡 (Winning Numbers + Jackpots)
                card1Html += `<div class="company-section" data-company="sabah_lotto"><div class="company-title">${name}${sharedImg}</div>${sharedDate}<div class="company-content">`;
                if (cd.winning_numbers && cd.winning_numbers.length > 0) {
                    card1Html += `<div class="subsection"><div class="subsection-title">Winning Numbers</div><div class="number-list">`;
                    cd.winning_numbers.forEach(n => card1Html += `<span class="number-item">${n}</span>`);
                    card1Html += `</div></div>`;
                }
                ['jackpot1', 'jackpot2'].forEach(f => {
                    if (cd[f] && typeof cd[f] === 'string' && cd[f].trim() !== '') {
                        card1Html += `<div class="subsection"><div class="subsection-title">${f.toUpperCase()}</div><div class="number-list"><span class="number-item" style="font-size:1.2rem;color:#d97706;font-weight:bold;">${cd[f]}</span></div></div>`;
                    }
                });
                card1Html += `</div></div>`;

                // 卡片2：6D Results
                let lt6gHtml = '';
                for (let g = 1; g <= 5; g++) {
                    let groupNums = [];
                    for (let i = 1; i <= 6; i++) {
                        if (cd[`LT6G${g}${i}`]) groupNums.push(cd[`LT6G${g}${i}`]);
                    }
                    if (groupNums.length > 0) {
                        lt6gHtml += `<div style="margin-bottom: 6px; display: flex; align-items: center; flex-wrap: wrap; gap: 4px;"><span style="font-size:0.8rem;color:#64748b;font-weight:600;width:50px;">Grp ${g}</span>` + groupNums.map(n => `<span class="number-item" style="font-size:1.1rem;padding:4px 8px;">${n}</span>`).join('') + `</div>`;
                    }
                }
                if (lt6gHtml) {
                    card2Html += `<div class="company-section" data-company="sabah_lotto_6d"><div class="company-title">SABAH LOTTO 6D Results${sharedImg}</div>${sharedDate}<div class="company-content"><div class="subsection"><div class="subsection-title">6D Results</div><div>${lt6gHtml}</div></div></div></div>`;
                    html += card2Html;
                }

                // 卡片3：5D Results
                let lt5gHtml = '';
                for (let g = 1; g <= 8; g++) {
                    let groupNums = [];
                    for (let i = 1; i <= 5; i++) {
                        if (cd[`LT5G${g}${i}`]) groupNums.push(cd[`LT5G${g}${i}`]);
                    }
                    if (groupNums.length > 0) {
                        lt5gHtml += `<div style="margin-bottom: 6px; display: flex; align-items: center; flex-wrap: wrap; gap: 4px;"><span style="font-size:0.8rem;color:#64748b;font-weight:600;width:50px;">Grp ${g}</span>` + groupNums.map(n => `<span class="number-item" style="font-size:1.1rem;padding:4px 8px;">${n}</span>`).join('') + `</div>`;
                    }
                }
                if (lt5gHtml) {
                    card3Html += `<div class="company-section" data-company="sabah_lotto_5d"><div class="company-title">SABAH LOTTO 5D Results${sharedImg}</div>${sharedDate}<div class="company-content"><div class="subsection"><div class="subsection-title">5D Results</div><div>${lt5gHtml}</div></div></div></div>`;
                    html += card3Html;
                }

                html += card1Html;
                rendered = true;
            }

            // ====== MAGNUM LIFE 专属布局 ======
            if (key === 'magnum_life') {
                if (cd.winning_numbers && cd.winning_numbers.length > 0) {
                    html += `<div class="subsection"><div class="subsection-title">Winning Numbers</div><div class="number-list">`;
                    cd.winning_numbers.forEach(n => html += `<span class="number-item">${n}</span>`);
                    html += `</div></div>`;
                }
                if (cd.bonus_numbers && cd.bonus_numbers.length > 0) {
                    html += `<div class="subsection"><div class="subsection-title">Bonus Numbers</div><div class="number-list">`;
                    cd.bonus_numbers.forEach(n => html += `<span class="number-item">${n}</span>`);
                    html += `</div></div>`;
                }
                rendered = true;
            }
            
            // ====== 其他特殊渲染（通用兼容） ======
            const winNums = cd.winning_numbers || cd.numbers || cd.results;
            if (!rendered && winNums && Array.isArray(winNums) && winNums.length > 0) { 
                html += `<div class="subsection"><div class="subsection-title">Winning Numbers</div><div class="number-list">`; 
                winNums.forEach(n=>html+=`<span class="number-item">${n}</span>`); 
                html += `</div></div>`; 
                rendered = true; 
            }
            
            if (!rendered && ['star','power','supreme'].some(f => cd[f] && Array.isArray(cd[f]) && cd[f].length > 0)) {
                ['star','power','supreme'].forEach(f=>{ 
                    if(cd[f]&&Array.isArray(cd[f])&&cd[f].length>0){ 
                        html += `<div class="subsection"><div class="subsection-title">${f.charAt(0).toUpperCase()+f.slice(1)}</div><div class="number-list">`; 
                        cd[f].forEach(n=>html+=`<span class="number-item">${n}</span>`); 
                        html += `</div></div>`; 
                        rendered = true; 
                    } 
                });
            }
            
            if (!rendered && (cd.jackpot||cd.jackpot1||cd.jackpot2)) {
                ['jackpot','jackpot1','jackpot2'].forEach(f=>{ 
                    if(cd[f]&&typeof cd[f]==='string'&&cd[f].trim()!==''){ 
                        html += `<div class="subsection"><div class="subsection-title">${f.toUpperCase()}</div><div class="number-list"><span class="number-item" style="font-size:1.2rem;color:#d97706;font-weight:bold;">${cd[f]}</span></div></div>`; 
                        rendered = true; 
                    } 
                });
            }
            
            if (!rendered) {
                const lt6g = Object.keys(cd).filter(k=>k.startsWith('LT6G')&&!k.endsWith('JP')&&cd[k]);
                if (lt6g.length > 0) { 
                    html += `<div class="subsection"><div class="subsection-title">6D Numbers</div><div class="number-list">`; 
                    lt6g.sort().forEach(k=>html+=`<span class="number-item">${cd[k]}</span>`); 
                    html += `</div></div>`; 
                    rendered = true; 
                }
            }
            
            if (!rendered) {
                html += `<div class="subsection"><div class="subsection-title">Results</div><div class="number-list"><span class="number-item" style="font-size:1rem;color:#888;">非开奖日 / 暂无记录</span></div></div>`;
            }
        } else {
            // 普通公司渲染保持不变
            html += `<div class="prize-grid"><div class="prize-card"><div class="label">First Prize</div><div class="number">${cd['1st']||'----'}</div></div><div class="prize-card"><div class="label">Second Prize</div><div class="number">${cd['2nd']||'----'}</div></div><div class="prize-card"><div class="label">Third Prize</div><div class="number">${cd['3rd']||'----'}</div></div></div>`;
            
            const validSpecial = cd.special ? cd.special.filter(n => n && n.trim() !== '' && n.trim() !== '****') : [];
            const validConsolation = cd.consolation ? cd.consolation.filter(n => n && n.trim() !== '' && n.trim() !== '****') : [];

            if (validSpecial.length > 0 || validConsolation.length > 0) { 
                html += `<div class="subsection">`; 
                if(validSpecial.length > 0){
                    html += `<div class="subsection-title">Special</div><div class="number-list">`;
                    validSpecial.forEach(n => html += `<span class="number-item">${n}</span>`);
                    html += `</div>`;
                }
                if(validConsolation.length > 0){
                    html += `<div class="subsection-title">Consolation</div><div class="number-list">`;
                    validConsolation.forEach(n => html += `<span class="number-item">${n}</span>`);
                    html += `</div>`;
                } 
                html += `</div>`; 
            } else if (cd['1st'] || cd['2nd'] || cd['3rd']) {
                html += `<div class="subsection"><div class="subsection-title">Special / Consolation</div><div class="number-list"><span class="number-item" style="font-size:1rem;color:#888;">待官方更新 / 暂无记录</span></div></div>`;
            }
        }
        html += `</div></div>`;
    });
    
    if (html === '') html = '<p style="text-align:center;grid-column:1/-1;color:#666;">当日暂无开奖数据</p>';
    grid.innerHTML = html;
}

// ==================== 日历组件逻辑 ====================
function initCalendar() {
    const popup = document.getElementById('calendar-popup'), btn = document.getElementById('calendar-btn');
    btn.addEventListener('click', e => { 
        e.stopPropagation(); 
        if(popup.style.display==='none'||popup.style.display===''){
            popup.style.display='block'; 
            renderCalendar();
        } else {
            popup.style.display='none'; 
        }
    });
    document.addEventListener('click', e => { if(!popup.contains(e.target)&&e.target!==btn) popup.style.display='none'; });
}

function renderCalendar() {
    const popup = document.getElementById('calendar-popup'); 
    const year = currentCalendarDate.getFullYear(), month = currentCalendarDate.getMonth();
    const firstDay = new Date(year, month, 1).getDay(), daysInMonth = new Date(year, month+1, 0).getDate();
    const monthNames = ["January","February","March","April","May","June","July","August","September","October","November","December"];
    
    let html = `<div class="calendar-header"><button class="calendar-nav" onclick="changeCalendarMonth(-1,event)">‹</button><span>${monthNames[month]} ${year}</span><button class="calendar-nav" onclick="changeCalendarMonth(1,event)">›</button></div><table class="calendar-table"><thead><tr><th>Su</th><th>Mo</th><th>Tu</th><th>We</th><th>Th</th><th>Fr</th><th>Sa</th></tr></thead><tbody>`;
    
    let day = 1;
    for (let i=0; i<6; i++) { 
        html += '<tr>'; 
        for(let j=0; j<7; j++){ 
            if(i===0&&j<firstDay){html+='<td></td>';} 
            else if(day>daysInMonth){html+='<td></td>';} 
            else { 
                const dateStr = `${year}-${String(month+1).padStart(2,'0')}-${String(day).padStart(2,'0')}`; 
                const has = availableDatesSet.has(dateStr), sel = dateStr===selectedDate; 
                html += `<td class="${has?'has-data':''} ${sel?'selected':''}" onclick="selectDateFromCalendar('${dateStr}',event)">${day}</td>`; 
                day++; 
            } 
        } 
        html += '</tr>'; 
        if(day>daysInMonth) break; 
    }
    popup.innerHTML = html + `</tbody></table>`;
}

window.changeCalendarMonth = (delta, e) => { 
    if(e) e.stopPropagation(); 
    currentCalendarDate.setMonth(currentCalendarDate.getMonth()+delta); 
    renderCalendar(); 
};

window.selectDateFromCalendar = (str, e) => { 
    if(e) e.stopPropagation(); 
    if(!availableDatesSet.has(str)) return; 
    selectedDate = str; 
    isFallbackMode = false; 
    document.getElementById('fallback-banner').style.display='none'; 
    document.getElementById('calendar-popup').style.display='none'; 
    updateDateBtnWithLatest(); 
    renderDateDropdown(); 
    fetchAndRenderData(str); 
};

// ==================== 初始化启动 ====================
document.addEventListener('DOMContentLoaded', () => {
    initCalendar();
    
    if (localStorage.getItem('darkMode')==='enabled') { 
        document.body.classList.add('dark-mode'); 
        document.getElementById('dark-mode-btn').innerHTML = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>'; 
    }
    
    const spinBtn = document.getElementById('spin-btn');
    if (spinBtn) {
        spinBtn.addEventListener('click', () => { 
            spinBtn.disabled = true; 
            let c = 0; 
            const int = setInterval(()=>{ 
                document.getElementById('digit1').innerText=Math.floor(Math.random()*10); 
                document.getElementById('digit2').innerText=Math.floor(Math.random()*10); 
                document.getElementById('digit3').innerText=Math.floor(Math.random()*10); 
                document.getElementById('digit4').innerText=Math.floor(Math.random()*10); 
                c++; 
                if(c>15){clearInterval(int);spinBtn.disabled=false;} 
            },80); 
        });
    }
    
    document.querySelectorAll('.modal-overlay').forEach(o => o.addEventListener('click', e => { if(e.target===e.currentTarget) o.style.display='none'; }));
    
    loadDateIndex();
});
