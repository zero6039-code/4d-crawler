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
    body.dark-mode .toto-5d-box .num { color: #fbbf24; text-shadow: 0 0 10px rgba(251,191,36,0.3); }

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
        box-shadow: 0 2px 8px rgba(198,40,40,0.3);
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
    .singapore-toto-table .toto-prize-row td { background: #fff7ed; color: #b45309; font-weight: 700; text-align: center; }
    body.dark-mode .singapore-toto-table .toto-prize-row td { background: rgba(120,53,15,0.45); color: #fbbf24; }
`;
const styleSheet = document.createElement("style");
styleSheet.textContent = totoStyles;
document.head.appendChild(styleSheet);

// ==================== 安全工具 ====================
const esc = s => String(s ?? '').replace(/[&<>"']/g,
  c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const asArr = v => Array.isArray(v) ? v : [];
const DATE_OK = /^\d{4}-\d{2}-\d{2}$/;

// ==================== 常量定义 ====================
// 【已调整顺序】SINGAPORE TOTO 已移至 DAMACAI 1+3D 之后，SABAH LOTTO 之前
const COMPANY_LIST = [
    'damacai', 'magnum', 'toto', 'singapore',
    'grand_dragon', 'perdana4d', 'lucky_hari',
    'sandakan', 'sarawak_cashsweep',
    'sabah', 'damacai_1p3d',
    'singapore_toto', 'sabah_lotto', 'sportstoto_lotto',
    'magnum_jackpot_gold', 'sportstoto_5d', 'sportstoto_6d',
    'magnum_life', 'sportstoto_fireball'
];

const NAME_MAP = {
    'grand_dragon': 'GRAND DRAGON 豪龙', 'damacai': 'DAMACAI 4D', 'magnum': 'MAGNUM 4D',
    'toto': 'TOTO 4D', 'singapore': 'SINGAPORE 4D', 'damacai_1p3d': 'DAMACAI 1+3D',
    'sandakan': 'SANDAKAN 4D', 'sarawak_cashsweep': 'SARAWAK CASH', 'sabah': 'SABAH 88 4D',
    'sabah_lotto': 'SABAH LOTTO', 'singapore_toto': 'SINGAPORE TOTO', 'sportstoto_lotto': 'SPORTS TOTO LOTTO',
    'magnum_jackpot_gold': 'MAGNUM JACKPOT GOLD', 'sportstoto_5d': 'SPORTS TOTO 5D',
    'sportstoto_6d': 'SPORTS TOTO 6D', 'magnum_life': 'MAGNUM LIFE', 'sportstoto_fireball': 'SPORTS TOTO FIREBALL',
    'perdana4d': 'PERDANA 4D',
    'lucky_hari': 'LUCKY 天天好运'
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
let dateDropdownBound = false, calendarBound = false;

// ==================== 日期工具函数 ====================
const ymdToDmy = ymd => { if(!ymd) return ''; let p = ymd.split('-'); return p.length===3 ? `${p[2]}-${p[1]}-${p[0]}` : ymd; };
const parseDMY = str => { let p = str.split('-'); let d,m,y; if(p[0].length===4){[y,m,d]=p.map(Number);}else{[d,m,y]=p.map(Number);} return {year:y,month:m,day:d}; };
const toSortKey = str => { let {year,month,day} = parseDMY(str); return year*10000+month*100+day; };
const sortDatesDesc = dates => dates.sort((a,b)=>toSortKey(b)-toSortKey(a));
const formatDisplayDate = str => { if(!str) return '加载中...'; let dmy = ymdToDmy(str); let p = dmy.split('-'); let d = new Date(p[2],p[1]-1,p[0]); return `${dmy} ${d.toLocaleDateString('en-US',{weekday:'short'})}`; };

