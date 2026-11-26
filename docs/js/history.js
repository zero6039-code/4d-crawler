/* docs/js/history.js — 号码历史查询（读取预生成索引） */
(function () {
    const PRIZES = [
        ['1st','头奖 | 1st'], ['2nd','二奖 | 2nd'], ['3rd','三奖 | 3rd'],
        ['special','特别奖 | Special'], ['consolation','安慰奖 | Consolation']
    ];
    const COMPANIES = ['sabah','sarawak_cashsweep','sandakan','lucky_hari','perdana4d',
        'grand_dragon','singapore','damacai','magnum','toto'];
    const LOGO = {
        sabah:'sabah88.png', sarawak_cashsweep:'sarawak.png', sandakan:'sandakan_logo.png',
        lucky_hari:'luckly_hari.png', perdana4d:'Perdana4D.png', grand_dragon:'granddragon.png',
        singapore:'singapore4d.png', damacai:'damacai.png', magnum:'magnum.png', toto:'toto.png'
    };
    const PAGE_SIZE = 20;
    let cache = null, loading = null, allRows = [], page = 1, pagesEl = null;

    function loadAll() {
        if (cache) return Promise.resolve(cache);
        if (loading) return loading;
        loading = fetch('data/history_index.json?t=' + Date.now(), { cache: 'no-store' })
            .then(r => { if (!r.ok) throw new Error('index'); return r.json(); })
            .then(j => (cache = j));
        return loading;
    }

    function esc(s) {
        return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    }

    function search(num) {
        const rows = [];
        for (const e of (cache[num] || [])) {
            const d = e[1];
            const date = String(Math.floor(d / 10000)).padStart(4, '0') + '-' +
                String(Math.floor(d / 100) % 100).padStart(2, '0') + '-' +
                String(d % 100).padStart(2, '0');
            const key = COMPANIES[e[2]] || '';
            rows.push({
                num, label: PRIZES[e[0]][1], pi: e[0], date,
                name: (typeof NAME_MAP !== 'undefined' && NAME_MAP[key]) || key,
                logo: LOGO[key] || ''
            });
        }
        rows.sort((a, b) => b.date.localeCompare(a.date) || a.pi - b.pi);
        return rows;
    }

    function rowHtml(r) {
        return `<div class="num-history-row">` +
            `<span>${esc(r.num)}</span><span>${esc(r.label)}</span>` +
            `<span>${esc(r.date)}</span><span>${esc(r.name)}</span>` +
            `<img src="images/${encodeURIComponent(r.logo)}" width="32" height="32" alt="">` +
            `</div>`;
    }

    function draw() {
        const out = document.getElementById('num-history-results');
        if (!out) return;
        const start = (page - 1) * PAGE_SIZE;
        out.innerHTML = allRows.slice(start, start + PAGE_SIZE).map(rowHtml).join('');
        const total = Math.ceil(allRows.length / PAGE_SIZE);
        if (!pagesEl) return;
        if (total <= 1) { pagesEl.innerHTML = ''; return; }
        let html = '';
        for (let i = 1; i <= total; i++) {
            html += `<button type="button" class="num-history-page${i === page ? ' active' : ''}" data-page="${i}">${i}</button>`;
        }
        pagesEl.innerHTML = html;
    }

    function render(rows, num) {
        allRows = rows; page = 1;
        const st = document.getElementById('num-history-status');
        const out = document.getElementById('num-history-results');
        if (!rows.length) {
            st.textContent = `无记录 / No record: ${num}`;
            out.innerHTML = '';
            if (pagesEl) pagesEl.innerHTML = '';
            return;
        }
        st.textContent = `${num} — ${rows.length} 条 | ${rows.length} items`;
        draw();
    }

    function clearAll() {
        const input = document.getElementById('num-history-input');
        const st = document.getElementById('num-history-status');
        const out = document.getElementById('num-history-results');
        if (input) input.value = '';
        if (st) st.textContent = '';
        if (out) out.innerHTML = '';
        if (pagesEl) pagesEl.innerHTML = '';
        allRows = []; page = 1;
    }

    async function run() {
        const input = document.getElementById('num-history-input');
        const st = document.getElementById('num-history-status');
        const num = (input.value || '').trim();
        const out = document.getElementById('num-history-results');
        out.innerHTML = '';
        if (pagesEl) pagesEl.innerHTML = '';
        if (!/^\d{4,6}$/.test(num)) {
            st.textContent = '请输入 4-6 位号码 / Enter 4-6 digits';
            return;
        }
        st.textContent = '加载中 / Loading…';
        try { await loadAll(); render(search(num), num); }
        catch (e) { st.textContent = '加载失败 / Load failed'; }
    }

    document.addEventListener('DOMContentLoaded', () => {
        const modal = document.getElementById('history-modal');
        const btn = document.getElementById('num-history-search-btn');
        const input = document.getElementById('num-history-input');
        const out = document.getElementById('num-history-results');
        if (out && !pagesEl) {
            pagesEl = document.createElement('div');
            pagesEl.className = 'num-history-pages';
            out.parentNode.appendChild(pagesEl);
            pagesEl.addEventListener('click', e => {
                const b = e.target.closest('[data-page]');
                if (!b) return;
                page = Number(b.dataset.page) || 1;
                draw();
            });
        }
        if (btn) btn.addEventListener('click', run);
        if (input) input.addEventListener('keydown', e => { if (e.key === 'Enter') run(); });
        if (modal) {
            const closeBtn = modal.querySelector('[data-action="close"]');
            if (closeBtn) closeBtn.addEventListener('click', clearAll);
            modal.addEventListener('click', e => { if (e.target === modal) clearAll(); });
        }
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape' && modal && modal.style.display === 'flex') {
                clearAll();
                if (typeof closeModal === 'function') closeModal('history-modal');
            }
        });
    });
})();

// 只接受 4 位数字
(function () {
  function init() {
    const el = document.getElementById('num-history-input');
    if (!el) return;
    const clean = () => { el.value = el.value.replace(/\D/g, '').slice(0, 4); };
    el.addEventListener('input', clean);
    el.addEventListener('paste', () => setTimeout(clean, 0));
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
