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
        const res = await fetch('data/dates.json', { cache: 'no-cache' });
        if (res.ok) {
            let dates = (await res.json()).filter(d => DATE_OK.test(d));
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
    container.innerHTML = availableDates.map(date =>
        `<div class="date-option${date===selectedDate?' active':''}" data-date="${esc(date)}">${esc(formatDisplayDate(date))}</div>`
    ).join('');
    if (!dateDropdownBound) {
        dateDropdownBound = true;
        container.addEventListener('click', e => {
            const el = e.target.closest('.date-option');
            if (el && el.dataset.date && DATE_OK.test(el.dataset.date)) selectDate(el.dataset.date);
        });
    }
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
    span.innerHTML = `${ind.outerHTML}${esc(text)}`;
    if (updateTime) document.getElementById('update-time').innerText = updateTime;
}

// ==================== 核心数据抓取与部分渲染 ====================
function hasAnyData(d) {
    if (!d) return false;
    for (const f of ['1st','2nd','3rd']) if (typeof d[f] === 'string' && d[f].trim() !== '') return true;
    for (const f of ['special','consolation','winning_numbers','star','power','supreme']) {
        if (Array.isArray(d[f]) && d[f].some(n => n && String(n).trim() !== '' && String(n).trim() !== '****')) return true;
    }
    for (const f of ['jackpot','jackpot1','jackpot2']) if (typeof d[f] === 'string' && d[f].trim() !== '') return true;
    if (d['2nd'] && typeof d['2nd'] === 'object' && d['2nd'].main) return true;
    return false;
}

async function loadAggregated(dateStr, isLatest, signal) {
    const url = isLatest ? 'data/latest.json' : `data/archive/${dateStr.slice(0, 7)}.json`;
    try {
        const res = await fetch(url, { cache: 'no-cache', signal });
        if (!res.ok) return null;
        const payload = await res.json();
        return isLatest ? payload : (payload[dateStr] || null);
    } catch { return null; }
}

let loadSeq = 0, loadCtl = null;
async function fetchAndRenderData(dateStr, isRefresh = false) {
    const seq = ++loadSeq;
    if (loadCtl) loadCtl.abort();
    loadCtl = new AbortController();
    const signal = loadCtl.signal;
    const grid = document.getElementById('companies-grid');
    grid.innerHTML = '<p style="text-align:center;grid-column:1/-1;color:#666;">🔄 正在加载数据...</p>';
    updateStatus('loading', '正在加载...');
    const isLatest = availableDates.length > 0 && dateStr === availableDates[0];

    const agg = await loadAggregated(dateStr, isLatest, signal);
    if (seq !== loadSeq) return;
    let dataMap = {}, validCount = 0;

    if (agg) {
        Object.keys(agg).forEach(key => {
            if (HIDDEN_COMPANIES.includes(key) || !COMPANY_LIST.includes(key)) return;
            const d = agg[key];
            if (hasAnyData(d)) { dataMap[key] = d; validCount++; }
        });
    } else {
        const promises = COMPANY_LIST.map(async key => {
            if (HIDDEN_COMPANIES.includes(key)) return { key, data: null };
            const basePath = isLatest ? `data` : `data/${dateStr}`;
            try {
                const res = await fetch(`${basePath}/${key}.json`, { cache: 'no-cache', signal });
                if (!res.ok) throw new Error();
                return { key, data: await res.json() };
            } catch { return { key, data: null }; }
        });
        const results = await Promise.all(promises);
        if (seq !== loadSeq) return;
        results.forEach(item => {
            if (hasAnyData(item.data)) { dataMap[item.key] = item.data; validCount++; }
        });
    }

    if (validCount === 0 && !isFallbackMode && availableDates.length > 1) {
        const idx = availableDates.indexOf(dateStr);
        if (idx >= 0 && idx + 1 < availableDates.length) {
            const fallbackDate = availableDates[idx + 1];
            document.getElementById('fallback-banner').innerHTML = `⚠️ <b>${esc(formatDisplayDate(dateStr))}</b> 暂无开奖数据，已自动为您显示 <b>${esc(formatDisplayDate(fallbackDate))}</b> 的最新成绩。`;
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
    updateStatus('success', '加载完成 · v1.2.3', `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')} ${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`);
}


// === UI patch 4: 60s incremental refresh ===
(function () {
    const POLL_MS = 60 * 1000;
    let lastStamp = null;
    const dateBtn = document.getElementById('date-btn');
    if (dateBtn) dateBtn.addEventListener('click', () => {
        dateBtn.classList.remove('has-new');
        dateBtn.removeAttribute('title');
    }, true);

    setInterval(async () => {
        if (document.visibilityState !== 'visible') return;
        try {
            const res = await fetch('data/dates.json?t=' + Date.now(), { cache: 'no-store' });
            if (!res.ok) return;
            const dates = sortDatesDesc((await res.json()).filter(d => DATE_OK.test(d)));
            const stamp = JSON.stringify(dates);
            if (lastStamp === null || stamp === lastStamp) { lastStamp = stamp; return; }
            lastStamp = stamp;
            if (stamp === JSON.stringify(availableDates)) return;

            const wasLatest = !!selectedDate && selectedDate === availableDates[0];
            availableDates = dates;
            availableDatesSet = new Set(dates);
            renderDateDropdown();

            if (wasLatest && dates.length) {
                selectedDate = dates[0];
                updateDateBtnWithLatest();
                fetchAndRenderData(selectedDate, true);
                if (dateBtn) { dateBtn.classList.remove('has-new'); dateBtn.removeAttribute('title'); }
            } else if (dates.length && dateBtn) {
                dateBtn.classList.add('has-new');
                dateBtn.title = '有新开奖数据';
            }
        } catch (e) { /* 静默失败，下一轮再试 */ }
    }, POLL_MS);
})();
