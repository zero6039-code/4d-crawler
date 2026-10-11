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

// ==================== 常量定义 ====================
// 【已按照你的要求调整顺序】：
// SINGAPORE 4D -> GRAND DRAGON -> Perdana -> Lucky HariHari -> SANDAKAN
// DAMACAI 1+3D 放在 SABAH 88 4D 后面
const COMPANY_LIST = [
    'damacai', 'magnum', 'toto', 'singapore', 
    'grand_dragon', 'perdana4d', 'lucky_hari', // 新增的 2 个卡片
    'sandakan', 'sarawak_cashsweep', 
    'sabah', 'damacai_1p3d', // DAMACAI 1+3D 已移到 SABAH 后面
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
    // 新增公司的名称
    'perdana4d': 'PERDANA LOTTERY 4D',
    'lucky_hari': 'LUCKY HARIHARI 天天好运'
};

// 注意：这里仅作为普通 4D 公司，如果你的新公司需要特殊渲染，请加入到 SPECIAL_COMPANIES 中
const SPECIAL_COMPANIES = ['sportstoto_fireball', 'singapore_toto', 'magnum_jackpot_gold', 'sportstoto_5d', 'sportstoto_6d', 'magnum_life', 'sportstoto_lotto', 'sabah_lotto'];
const HIDDEN_COMPANIES = ['sportstoto_fireball'];

const COMPANY_IMAGE_MAP = {
    'damacai': 'damacai.png', 'damacai_1p3d': 'damacai1+3.png', 'sandakan': 'sandakan_logo.png',
    'sarawak_cashsweep': 'sarawak.png', 'sabah': 'sabah88.png', 'sabah_lotto': 'sabahlotto.png',
    'grand_dragon': 'granddragon.png', 'magnum': 'magnum.png', 'toto': 'toto.png',
    'singapore': 'singapore4d.png', 'singapore_toto': 'singapore-pools.png',
    // 新增公司的 Logo
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
            
            // 1. 检查主要号码字段 (1st, 2nd, 3rd)
            ['1st', '2nd', '3rd'].forEach(f => {
                if (item.data[f] && typeof item.data[f] === 'string' && item.data[f].trim() !== '') hasData = true;
            });
            
            // 2. 检查数组类字段 (special, consolation, winning_numbers, star, power, supreme)
            ['special', 'consolation', 'winning_numbers', 'star', 'power', 'supreme'].forEach(f => {
                if (item.data[f] && Array.isArray(item.data[f]) && item.data[f].some(n => n && n.trim() !== '' && n.trim() !== '****')) hasData = true;
            });

            // 3. 检查 jackpot 类字段
            ['jackpot', 'jackpot1', 'jackpot2'].forEach(f => {
                if (item.data[f] && typeof item.data[f] === 'string' && item.data[f].trim() !== '') hasData = true;
            });

            // 4. 检查 6D 特殊结构字段 (例如 cd['2nd'].main 存在)
            if (item.data['2nd'] && typeof item.data['2nd'] === 'object' && item.data['2nd'].main) hasData = true;

            if (hasData) { dataMap[item.key] = item.data; validCount++; }
        }
    });

    // 自动回退逻辑
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
            // 优化 5D 判断
            const is5D = cd.type === '5d' || (!cd.type && cd['6th'] && (!cd['2nd'] || typeof cd['2nd'] === 'string'));
            if (is5D) { 
                html += `<div class="subsection"><div class="subsection-title">5D Results</div><div class="number-list">`; 
                ['1st','2nd','3rd','4th','5th','6th'].forEach(k=>{ 
                    if(cd[k] && cd[k].trim() !== '') html += `<span class="number-item">${cd[k]}</span>`; 
                }); 
                html += `</div></div>`; 
                rendered = true; 
            }
            
            // 优化 6D 判断
            const is6D = cd.type === '6d' || (!cd.type && cd['2nd'] && cd['2nd'].main);
            if (is6D) { 
                html += `<div class="subsection"><div class="subsection-title">6D Results</div><div class="number-list">`; 
                if(cd['1st'] && cd['1st'].trim() !== '') html += `<span class="number-item">${cd['1st']}</span>`; 
                ['2nd','3rd','4th','5th'].forEach(k=>{ 
                    if(cd[k]) { 
                        if(typeof cd[k]==='object'&&cd[k].main) html += `<span class="number-item">${cd[k].main} / ${cd[k].alt}</span>`; 
                        else if(typeof cd[k]==='string' && cd[k].trim() !== '') html += `<span class="number-item">${cd[k]}</span>`; 
                    } 
                }); 
                html += `</div></div>`; 
                rendered = true; 
            }
            
            const winNums = cd.winning_numbers || cd.numbers || cd.results;
            if (winNums && Array.isArray(winNums) && winNums.length > 0) { 
                html += `<div class="subsection"><div class="subsection-title">Winning Numbers</div><div class="number-list">`; 
                winNums.forEach(n=>html+=`<span class="number-item">${n}</span>`); 
                html += `</div></div>`; 
                rendered = true; 
            }
            
            ['star','power','supreme'].forEach(f=>{ 
                if(cd[f]&&Array.isArray(cd[f])&&cd[f].length>0){ 
                    html += `<div class="subsection"><div class="subsection-title">${f.charAt(0).toUpperCase()+f.slice(1)}</div><div class="number-list">`; 
                    cd[f].forEach(n=>html+=`<span class="number-item">${n}</span>`); 
                    html += `</div></div>`; 
                    rendered = true; 
                } 
            });
            
            ['jackpot','jackpot1','jackpot2'].forEach(f=>{ 
                if(cd[f]&&typeof cd[f]==='string'&&cd[f].trim()!==''){ 
                    html += `<div class="subsection"><div class="subsection-title">${f.toUpperCase()}</div><div class="number-list"><span class="number-item" style="font-size:1.2rem;color:#d97706;font-weight:bold;">${cd[f]}</span></div></div>`; 
                    rendered = true; 
                } 
            });
            
            const lt6g = Object.keys(cd).filter(k=>k.startsWith('LT6G')&&!k.endsWith('JP')&&cd[k]);
            if (lt6g.length > 0) { 
                html += `<div class="subsection"><div class="subsection-title">6D Numbers</div><div class="number-list">`; 
                lt6g.sort().forEach(k=>html+=`<span class="number-item">${cd[k]}</span>`); 
                html += `</div></div>`; 
                rendered = true; 
            }
            
            if (!rendered) {
                html += `<div class="subsection"><div class="subsection-title">Results</div><div class="number-list"><span class="number-item" style="font-size:1rem;color:#888;">非开奖日 / 暂无记录</span></div></div>`;
            }
        } else {
            // 普通公司：任何缺失的字段都显示 ----
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
    
    document.querySelectorAll('.modal-overlay').forEach(o => o.addEventListener('click', e => { if(e.target===o) o.style.display='none'; }));
    
    loadDateIndex();
});
