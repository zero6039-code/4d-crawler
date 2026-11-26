// ==================== 智能渲染公司卡片 ====================
function renderCompanies(dataMap) {
    const grid = document.getElementById('companies-grid'); let html = '';

    COMPANY_LIST.forEach(key => {
        if (HIDDEN_COMPANIES.includes(key)) return;
        const cd = dataMap[key]; if (!cd) return;
        const mark = html.length; // 失败回滚点
        try {
        const name = NAME_MAP[key] || key;
        const img = COMPANY_IMAGE_MAP[key] ? `images/${COMPANY_IMAGE_MAP[key]}` : null;

        // SABAH LOTTO 提前返回，独立生成3个卡片
        if (key === 'sabah_lotto') {
            const sharedDate = `<div class="draw-date">${esc(cd.draw_date || '未知')} ${cd.draw_no?'| Draw No: '+esc(cd.draw_no):''}</div>`;
            const sharedImg = img ? `<img src="${img}">` : '';
            let sabahCardsHtml = '';

            // 1. 主卡片 (Winning Numbers + Jackpots)
            sabahCardsHtml += `<div class="company-section" data-company="sabah_lotto"><div class="company-title">${name}${sharedImg}</div>${sharedDate}<div class="company-content">`;
            if (asArr(cd.winning_numbers).length > 0) {
                sabahCardsHtml += `<div class="subsection"><div class="subsection-title">Winning Numbers</div><div class="number-list">`;
                asArr(cd.winning_numbers).forEach(n => sabahCardsHtml += `<span class="number-item">${esc(n)}</span>`);
                sabahCardsHtml += `</div></div>`;
            }
            ['jackpot1', 'jackpot2'].forEach(f => {
                if (cd[f] && typeof cd[f] === 'string' && cd[f].trim() !== '') {
                    sabahCardsHtml += `<div class="subsection"><div class="subsection-title">${f.toUpperCase()}</div><div class="number-list"><span class="number-item" style="font-size:1.2rem;color:#d97706;font-weight:bold;">${esc(cd[f])}</span></div></div>`;
                }
            });
            sabahCardsHtml += `</div></div>`;

            // 2. 6D 卡片
            let lt6gHtml = '';
            for (let g = 1; g <= 5; g++) {
                let groupNums = [];
                for (let i = 1; i <= 6; i++) {
                    if (cd[`LT6G${g}${i}`]) groupNums.push(cd[`LT6G${g}${i}`]);
                }
                if (groupNums.length > 0) {
                    lt6gHtml += `<div style="margin-bottom: 6px; display: flex; align-items: center; flex-wrap: wrap; gap: 4px;"><span style="font-size:0.8rem;color:#64748b;font-weight:600;width:50px;">Grp ${g}</span>` + groupNums.map(n => `<span class="number-item" style="font-size:1.1rem;padding:4px 8px;">${esc(n)}</span>`).join('') + `</div>`;
                }
            }
            if (lt6gHtml) {
                sabahCardsHtml += `<div class="company-section" data-company="sabah_lotto_6d"><div class="company-title">SABAH LOTTO 6D${sharedImg}</div>${sharedDate}<div class="company-content"><div class="subsection"><div class="subsection-title">6D Results</div><div>${lt6gHtml}</div></div></div></div>`;
            }

            // 3. 5D 卡片
            let lt5gHtml = '';
            for (let g = 1; g <= 8; g++) {
                let groupNums = [];
                for (let i = 1; i <= 5; i++) {
                    if (cd[`LT5G${g}${i}`]) groupNums.push(cd[`LT5G${g}${i}`]);
                }
                if (groupNums.length > 0) {
                    lt5gHtml += `<div style="margin-bottom: 6px; display: flex; align-items: center; flex-wrap: wrap; gap: 4px;"><span style="font-size:0.8rem;color:#64748b;font-weight:600;width:50px;">Grp ${g}</span>` + groupNums.map(n => `<span class="number-item" style="font-size:1.1rem;padding:4px 8px;">${esc(n)}</span>`).join('') + `</div>`;
                }
            }
            if (lt5gHtml) {
                sabahCardsHtml += `<div class="company-section" data-company="sabah_lotto_5d"><div class="company-title">SABAH LOTTO 5D${sharedImg}</div>${sharedDate}<div class="company-content"><div class="subsection"><div class="subsection-title">5D Results</div><div>${lt5gHtml}</div></div></div></div>`;
            }

            html += sabahCardsHtml;
            return; // 跳过下方所有包裹和通用渲染逻辑
        }

        // --- 下面开始是其他卡片的通用渲染逻辑 ---
        const timeTag = cd.draw_time ? ` | <span style="color: #d97706; font-weight: bold;">${esc(cd.draw_time)}</span>` : '';
        html += `<div class="company-section" data-company="${esc(key)}"><div class="company-title">${name}${img?`<img src="${img}">`:''}</div><div class="draw-date">${esc(cd.draw_date || '未知')} ${cd.draw_no?'| Draw No: '+esc(cd.draw_no):''}${timeTag}</div><div class="company-content">`;

        const isSpecial = SPECIAL_COMPANIES.includes(key);

        if (isSpecial) {
            let rendered = false;

            // 5D 专属布局
            const is5D = cd.type === '5d' || (!cd.type && cd['6th'] && (!cd['2nd'] || typeof cd['2nd'] === 'string'));
            if (is5D) {
                html += `<div class="subsection"><div class="subsection-title">5D Results</div><div class="toto-5d-grid">`;
                const labels = [['1st', '2nd'], ['3rd', '4th'], ['5th', '6th']];
                labels.forEach(row => {
                    row.forEach(lbl => {
                        if (cd[lbl]) {
                            html += `<div class="toto-5d-box">
                                        <div class="label">${lbl}</div>
                                        <div class="num">${esc(cd[lbl])}</div>
                                     </div>`;
                        }
                    });
                });
                html += `</div></div>`;
                rendered = true;
            }

            // 6D 专属布局
            const is6D = cd.type === '6d' || (!cd.type && cd['2nd'] && cd['2nd'].main);
            if (is6D) {
                html += `<div class="subsection"><div class="subsection-title">6D Results</div><div class="toto-6d-grid">`;
                if (cd['1st']) {
                    html += `<div class="toto-6d-row">
                                <span class="label">1st</span>
                                <span class="main-num">${esc(cd['1st'])}</span>
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
                                    <span class="main-num">${esc(main)}</span>`;
                        if (alt !== '----') {
                            html += `<span class="or-text">or</span>
                                     <span class="alt-num">${esc(alt)}</span>`;
                        }
                        html += `<span style="flex:1;"></span>
                                 </div>`;
                    }
                });
                html += `</div></div>`;
                rendered = true;
            }

            // Singapore Toto 专属布局
            if (key === 'singapore_toto') {
                if (asArr(cd.winning_numbers).length > 0) {
                    html += `<div class="subsection"><div class="subsection-title">Winning Numbers</div><div class="toto-ball-row">`;
                    asArr(cd.winning_numbers).forEach((num, index) => {
                        if (index === asArr(cd.winning_numbers).length - 1) {
                            html += `<div class="toto-special-ball">${esc(num)}</div>`;
                        } else {
                            html += `<div class="toto-ball">${esc(num)}</div>`;
                        }
                    });
                    html += `</div></div>`;
                }
                if (asArr(cd.prize_table).filter(Array.isArray).length > 0) {
                    html += `<div class="subsection"><div class="subsection-title">Prize Table</div>`;
                    html += `<table class="singapore-toto-table">
                                <thead><tr><th>Prize Group</th><th>Share Amount (Each)</th><th>No. of Winning Shares</th></tr></thead>
                                <tbody>`;
                    asArr(cd.prize_table).filter(Array.isArray).forEach(row => {
                        html += `<tr>`;
                        asArr(row).forEach(cell => html += `<td>${esc(cell)}</td>`);
                        html += `</tr>`;
                    });
                    if (cd.prize && typeof cd.prize === 'string' && cd.prize.trim() !== '') {
                        html += `<tr class="toto-prize-row"><td colspan="3">Prize: ${esc(cd.prize)}</td></tr>`;
                    }
                    html += `</tbody></table></div>`;
                }
                rendered = true;
            }

            // SPORTS TOTO LOTTO 专属布局
            if (key === 'sportstoto_lotto') {
                const lottoGroups = [
                    { field: 'star', title: 'Star', jpIdx: 0, jpName: 'Jackpot 1' },
                    { field: 'power', title: 'Power', jpIdx: 2, jpName: 'Jackpot' },
                    { field: 'supreme', title: 'Supreme', jpIdx: 3, jpName: 'Jackpot' }
                ];
                lottoGroups.forEach(g => {
                    if (cd[g.field] && Array.isArray(cd[g.field]) && cd[g.field].length > 0) {
                        html += `<div class="subsection"><div class="subsection-title">${g.title}</div><div class="number-list">`;
                        cd[g.field].forEach(n => html += `<span class="number-item">${esc(n)}</span>`);
                        html += `</div>`;
                        if (String((cd.jackpots || {})[g.jpIdx] ?? '').trim() !== '') {
                            html += `<div style="margin-top: 8px; font-weight: 700; color: #d97706; font-size: 1rem;">${g.jpName}: ${esc((cd.jackpots || {})[g.jpIdx])}</div>`;
                        }
                        html += `</div>`;
                        rendered = true;
                    }
                });
            }

            // MAGNUM LIFE 专属布局
            if (key === 'magnum_life') {
                if (asArr(cd.winning_numbers).length > 0) {
                    html += `<div class="subsection"><div class="subsection-title">Winning Numbers</div><div class="number-list">`;
                    asArr(cd.winning_numbers).forEach(n => html += `<span class="number-item">${esc(n)}</span>`);
                    html += `</div></div>`;
                }
                if (asArr(cd.bonus_numbers).length > 0) {
                    html += `<div class="subsection"><div class="subsection-title">Bonus Numbers</div><div class="number-list">`;
                    asArr(cd.bonus_numbers).forEach(n => html += `<span class="number-item">${esc(n)}</span>`);
                    html += `</div></div>`;
                }
                rendered = true;
            }

            // 其他通用渲染
            const winNums = cd.winning_numbers || cd.numbers || cd.results;
            if (!rendered && winNums && Array.isArray(winNums) && winNums.length > 0) {
                html += `<div class="subsection"><div class="subsection-title">Winning Numbers</div><div class="number-list">`;
                winNums.forEach(n=>html+=`<span class="number-item">${esc(n)}</span>`);
                html += `</div></div>`;
                rendered = true;
            }

            if (!rendered && ['star','power','supreme'].some(f => cd[f] && Array.isArray(cd[f]) && cd[f].length > 0)) {
                ['star','power','supreme'].forEach(f=>{
                    if(cd[f]&&Array.isArray(cd[f])&&cd[f].length>0){
                        html += `<div class="subsection"><div class="subsection-title">${f.charAt(0).toUpperCase()+f.slice(1)}</div><div class="number-list">`;
                        cd[f].forEach(n=>html+=`<span class="number-item">${esc(n)}</span>`);
                        html += `</div></div>`;
                        rendered = true;
                    }
                });
            }

            if (!rendered && (cd.jackpot||cd.jackpot1||cd.jackpot2)) {
                ['jackpot','jackpot1','jackpot2'].forEach(f=>{
                    if(cd[f]&&typeof cd[f]==='string'&&cd[f].trim()!==''){
                        html += `<div class="subsection"><div class="subsection-title">${f.toUpperCase()}</div><div class="number-list"><span class="number-item" style="font-size:1.2rem;color:#d97706;font-weight:bold;">${esc(cd[f])}</span></div></div>`;
                        rendered = true;
                    }
                });
            }

            if (!rendered) {
                const lt6g = Object.keys(cd).filter(k=>k.startsWith('LT6G')&&!k.endsWith('JP')&&cd[k]);
                if (lt6g.length > 0) {
                    html += `<div class="subsection"><div class="subsection-title">6D Numbers</div><div class="number-list">`;
                    lt6g.sort().forEach(k=>html+=`<span class="number-item">${esc(cd[k])}</span>`);
                    html += `</div></div>`;
                    rendered = true;
                }
            }

            if (!rendered) {
                html += `<div class="subsection"><div class="subsection-title">Results</div><div class="number-list"><span class="number-item" style="font-size:1rem;color:#888;">非开奖日 / 暂无记录</span></div></div>`;
            }
        } else {
            // 普通公司渲染
            html += `<div class="prize-grid"><div class="prize-card"><div class="label">First Prize</div><div class="number">${esc(cd['1st']||'----')}</div></div><div class="prize-card"><div class="label">Second Prize</div><div class="number">${esc(cd['2nd']||'----')}</div></div><div class="prize-card"><div class="label">Third Prize</div><div class="number">${esc(cd['3rd']||'----')}</div></div></div>`;

            const validSpecial = asArr(cd.special).filter(n => n && String(n).trim() !== '' && String(n).trim() !== '****');
            const validConsolation = asArr(cd.consolation).filter(n => n && String(n).trim() !== '' && String(n).trim() !== '****');

            if (validSpecial.length > 0 || validConsolation.length > 0) {
                html += `<div class="subsection">`;
                if(validSpecial.length > 0){
                    html += `<div class="subsection-title">Special</div><div class="number-list">`;
                    validSpecial.forEach(n => html += `<span class="number-item">${esc(n)}</span>`);
                    html += `</div>`;
                }
                if(validConsolation.length > 0){
                    html += `<div class="subsection-title">Consolation</div><div class="number-list">`;
                    validConsolation.forEach(n => html += `<span class="number-item">${esc(n)}</span>`);
                    html += `</div>`;
                }
                html += `</div>`;
            } else if (cd['1st'] || cd['2nd'] || cd['3rd']) {
                html += `<div class="subsection"><div class="subsection-title">Special / Consolation</div><div class="number-list"><span class="number-item" style="font-size:1rem;color:#888;">待官方更新 / 暂无记录</span></div></div>`;
            }
        }
        html += `</div></div>`;
    } catch (e) {
        html = html.slice(0, mark); // 不留半截 HTML
        console.error('渲染失败:', key, e);
    }
    });

    if (html === '') html = '<p style="text-align:center;grid-column:1/-1;color:#666;">当日暂无开奖数据</p>';
    grid.innerHTML = html;
    grid.querySelectorAll('img').forEach(img => img.addEventListener('error', () => { img.style.display = 'none'; }));
}

