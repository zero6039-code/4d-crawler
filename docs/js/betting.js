// ========== 模拟下注游戏（本地匿名状态，无账号/密码/邮箱） ==========
(function () {
    'use strict';

    const STATE_KEY = 'betting_state_v1';
    const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

    class BettingGame {
        constructor() {
            this.state = this.loadState();
            this.drawDate = '';
            this.checkWeeklyGrant();
            this.bindEvents();
        }

        loadState() {
            try {
                const raw = localStorage.getItem(STATE_KEY);
                const s = raw ? JSON.parse(raw) : null;
                if (s && typeof s === 'object') {
                    return {
                        balance: Number(s.balance) || 0,
                        history: Array.isArray(s.history) ? s.history : [],
                        lastGrantWeek: s.lastGrantWeek || null
                    };
                }
            } catch (_) { /* 损坏数据直接重置 */ }
            return { balance: 0, history: [], lastGrantWeek: null };
        }

        saveState() {
            try { localStorage.setItem(STATE_KEY, JSON.stringify(this.state)); } catch (_) {}
        }

        checkWeeklyGrant() {
            const now = new Date();
            const day = now.getDay();
            const monday = new Date(now);
            monday.setDate(now.getDate() - (day === 0 ? 6 : day - 1));
            monday.setHours(8, 0, 0, 0);
            const last = this.state.lastGrantWeek ? new Date(this.state.lastGrantWeek) : null;
            if (!last || last < monday) {
                this.state.balance += 100;
                this.state.lastGrantWeek = monday.toISOString();
                this.saveState();
            }
        }

        setDrawDate(date) {
            if (!DATE_RE.test(date || '')) return false;
            this.drawDate = date;
            return true;
        }

        placeBet(company, betType, amount, numbers, drawResult, drawDate) {
            if (!DATE_RE.test(drawDate || '')) return { success: false, message: '缺少或非法开奖日期' };
            this.drawDate = drawDate;
            amount = Number(amount);
            if (!Number.isFinite(amount) || amount <= 0 || amount > 100) return { success: false, message: '下注金额须在 1-100 RM 之间' };
            if (!/^\d{4}$/.test(numbers || '')) return { success: false, message: '请输入4位数字号码' };
            if (this.state.balance < amount) return { success: false, message: '余额不足' };

            let prize = 0, prizeName = null;
            if (drawResult && typeof drawResult === 'object') {
                const big = betType === 'BIG';
                if (numbers === drawResult['1st']) { prize = amount * (big ? 2500 : 3500); prizeName = '头奖'; }
                else if (numbers === drawResult['2nd']) { prize = amount * (big ? 1000 : 2000); prizeName = '二奖'; }
                else if (numbers === drawResult['3rd']) { prize = amount * (big ? 500 : 1000); prizeName = '三奖'; }
                else if (Array.isArray(drawResult.special) && drawResult.special.includes(numbers)) { prize = amount * (big ? 180 : 0); prizeName = '特别奖'; }
                else if (Array.isArray(drawResult.consolation) && drawResult.consolation.includes(numbers)) { prize = amount * (big ? 60 : 0); prizeName = '安慰奖'; }
            }

            this.state.balance -= amount;
            const record = {
                date: new Date().toISOString(),
                drawDate: drawDate,
                company: String(company || '').slice(0, 40),
                type: String(betType || '').slice(0, 20),
                numbers: numbers,
                amount: amount,
                prize: prize,
                prizeName: prizeName,
                result: prize > 0 ? `🎉 中奖 ${prizeName} +${prize} RM` : '未中奖'
            };
            this.state.history.unshift(record);
            if (prize > 0) this.state.balance += prize;
            this.saveState();
            return { success: true, prize: prize, prizeName: prizeName, newBalance: this.state.balance, record: record };
        }

        updateUI() {
            const bal = document.getElementById('balance-display');
            if (bal) bal.textContent = this.state.balance.toFixed(2);
            this.renderHistory();
        }

        renderHistory() {
            const box = document.getElementById('bet-history-list');
            if (!box) return;
            box.textContent = '';
            if (!this.state.history.length) {
                const p = document.createElement('p');
                p.className = 'loading-history';
                p.textContent = '暂无投注记录';
                box.appendChild(p);
                return;
            }
            this.state.history.slice(0, 20).forEach(rec => {
                const div = document.createElement('div');
                div.className = 'history-item';
                const line1 = document.createElement('div');
                line1.textContent = `${String(rec.company || '').toUpperCase()} ${rec.type || ''} | ${rec.numbers} | ${rec.drawDate || ''}`;
                const line2 = document.createElement('div');
                line2.textContent = `下注: ${rec.amount} RM | ${rec.result || ''}`;
                div.appendChild(line1);
                div.appendChild(line2);
                box.appendChild(div);
            });
        }

        exportData() {
            const data = { balance: this.state.balance, history: this.state.history, exportTime: new Date().toISOString() };
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `betting_${Date.now()}.json`;
            a.click();
            URL.revokeObjectURL(url);
        }

        clearHistory() {
            if (confirm('确定要清空所有投注记录吗？')) {
                this.state.history = [];
                this.saveState();
                this.renderHistory();
            }
        }

        bindEvents() {
            document.addEventListener('DOMContentLoaded', () => {
                const placeBetBtn = document.getElementById('place-bet-btn');
                if (placeBetBtn) {
                    placeBetBtn.addEventListener('click', async () => {
                        if (!this.drawDate) { alert('请先指定开奖日期'); return; }
                        const company = document.getElementById('bet-company').value;
                        const betType = document.getElementById('bet-type').value;
                        const amount = parseFloat(document.getElementById('bet-amount').value);
                        const numbers = document.getElementById('bet-number').value.trim();
                        const url = `data/${this.drawDate}/${company}.json?t=${Date.now()}`;
                        let drawResult = null;
                        try { const res = await fetch(url); if (res.ok) drawResult = await res.json(); } catch (_) {}
                        const result = this.placeBet(company, betType, amount, numbers, drawResult, this.drawDate);
                        alert(result.success
                            ? `下注 ${amount} RM，号码 ${numbers}${result.prize > 0 ? ` 🎉 中奖 +${result.prize} RM` : ' ❌ 未中奖'}`
                            : result.message);
                        if (result.success) { this.updateUI(); document.getElementById('bet-number').value = ''; }
                    });
                }
                const exportBtn = document.getElementById('export-data-btn');
                if (exportBtn) exportBtn.addEventListener('click', () => this.exportData());
                const clearBtn = document.getElementById('clear-history-btn');
                if (clearBtn) clearBtn.addEventListener('click', () => this.clearHistory());
            });
        }
    }

    const game = new BettingGame();
    window.bettingGame = game;
})();
