// ========== 模拟下注游戏 ==========
(function() {
    class BettingGame {
        constructor() {
            this.currentUser = null;
            this.users = this.loadUsers();
            this.init();
        }
        
        loadUsers() {
            const stored = localStorage.getItem('betting_users');
            return stored ? JSON.parse(stored) : {};
        }
        
        saveUsers() {
            localStorage.setItem('betting_users', JSON.stringify(this.users));
        }
        
        checkWeeklyGrant(user) {
            if (!user) return user;
            const now = new Date();
            const day = now.getDay();
            let lastMonday = new Date(user.lastGrantWeek);
            let currentMonday = new Date(now);
            currentMonday.setDate(now.getDate() - (day === 0 ? 6 : day - 1));
            currentMonday.setHours(8, 0, 0, 0);
            lastMonday.setHours(8, 0, 0, 0);
            
            if (!user.lastGrantWeek || lastMonday < currentMonday) {
                user.balance = (user.balance || 0) + 100;
                user.lastGrantWeek = currentMonday.toISOString();
                this.users[user.username] = user;
                this.saveUsers();
            }
            return user;
        }
        
        register(username, password, email) {
            if (this.users[username]) return null;
            const newUser = {
                username: username,
                password: password,
                email: email,
                balance: 100,
                history: [],
                lastGrantWeek: new Date().toISOString()
            };
            this.users[username] = newUser;
            this.saveUsers();
            return newUser;
        }
        
        login(username, password, remember = false) {
            if (!username || !password) return null;
            let user = this.users[username];
            if (!user) {
                user = this.register(username, password, '');
                if (!user) return null;
            } else if (user.password !== password) {
                return null;
            }
            user = this.checkWeeklyGrant(user);
            this.currentUser = user;
            if (remember) {
                localStorage.setItem('rememberedUser', username);
                localStorage.setItem('rememberedPass', password);
            } else {
                localStorage.removeItem('rememberedUser');
                localStorage.removeItem('rememberedPass');
            }
            return user;
        }
        
        resetPassword(username, email, newPassword) {
            const user = this.users[username];
            if (user && user.email === email) {
                user.password = newPassword;
                this.saveUsers();
                return true;
            }
            return false;
        }
        
        placeBet(company, betType, amount, numbers, drawResult) {
            if (!this.currentUser) return { success: false, message: '请先登录' };
            if (amount <= 0 || amount > 100) return { success: false, message: '下注金额须在 1-100 RM 之间' };
            if (!/^\d{4}$/.test(numbers)) return { success: false, message: '请输入4位数字号码' };
            if (this.currentUser.balance < amount) return { success: false, message: '余额不足' };
            
            let prize = 0;
            let prizeName = null;
            const num = numbers;
            const type = betType;
            
            if (drawResult) {
                if (num === drawResult['1st']) {
                    prize = amount * (type === 'BIG' ? 2500 : 3500);
                    prizeName = '头奖';
                } else if (num === drawResult['2nd']) {
                    prize = amount * (type === 'BIG' ? 1000 : 2000);
                    prizeName = '二奖';
                } else if (num === drawResult['3rd']) {
                    prize = amount * (type === 'BIG' ? 500 : 1000);
                    prizeName = '三奖';
                } else if (drawResult.special && drawResult.special.includes(num)) {
                    prize = amount * (type === 'BIG' ? 180 : 0);
                    prizeName = '特别奖';
                } else if (drawResult.consolation && drawResult.consolation.includes(num)) {
                    prize = amount * (type === 'BIG' ? 60 : 0);
                    prizeName = '安慰奖';
                }
            }
            
            this.currentUser.balance -= amount;
            
            const record = {
                date: new Date().toISOString(),
                company: company,
                type: betType,
                numbers: numbers,
                amount: amount,
                prize: prize,
                prizeName: prizeName,
                result: prize > 0 ? `🎉 中奖 ${prizeName} +${prize} RM` : '未中奖'
            };
            this.currentUser.history.unshift(record);
            
            if (prize > 0) {
                this.currentUser.balance += prize;
                record.result = `🎉 中奖 ${prizeName} +${prize} RM`;
            }
            
            this.users[this.currentUser.username] = this.currentUser;
            this.saveUsers();
            
            return {
                success: true,
                prize: prize,
                prizeName: prizeName,
                newBalance: this.currentUser.balance,
                record: record
            };
        }
        
        updateUI() {
            if (this.currentUser) {
                document.getElementById('username-display').innerText = this.currentUser.username;
                document.getElementById('balance-display').innerText = this.currentUser.balance.toFixed(2);
                this.renderHistory();
            }
        }
        
        renderHistory() {
            const container = document.getElementById('bet-history-list');
            if (!this.currentUser || !this.currentUser.history.length) {
                container.innerHTML = '<p class="loading-history">暂无投注记录</p>';
                return;
            }
            const html = this.currentUser.history.slice(0, 20).map(rec => `
                <div class="history-item">
                    <div><strong>${rec.company.toUpperCase()} ${rec.type}</strong> | ${rec.numbers}</div>
                    <div>下注: ${rec.amount} RM | ${rec.result}</div>
                    <div class="history-date">${new Date(rec.date).toLocaleString()}</div>
                </div>
            `).join('');
            container.innerHTML = html;
        }
        
        exportData() {
            if (!this.currentUser) return;
            const exportData = {
                username: this.currentUser.username,
                balance: this.currentUser.balance,
                history: this.currentUser.history,
                exportTime: new Date().toISOString()
            };
            const dataStr = JSON.stringify(exportData, null, 2);
            const blob = new Blob([dataStr], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `betting_${this.currentUser.username}_${Date.now()}.json`;
            a.click();
            URL.revokeObjectURL(url);
        }
        
        clearHistory() {
            if (!this.currentUser) return;
            if (confirm('确定要清空所有投注记录吗？')) {
                this.currentUser.history = [];
                this.users[this.currentUser.username] = this.currentUser;
                this.saveUsers();
                this.renderHistory();
            }
        }
        
        init() {
            const rememberedUser = localStorage.getItem('rememberedUser');
            const rememberedPass = localStorage.getItem('rememberedPass');
            if (rememberedUser && rememberedPass) {
                this.login(rememberedUser, rememberedPass, true);
            }
        }
    }
    
    const game = new BettingGame();
    
    // 绑定弹窗按钮（需要等 DOM 加载完成）
    document.addEventListener('DOMContentLoaded', () => {
        const bettingBtn = document.getElementById('betting-btn');
        const modal = document.getElementById('betting-modal');
        const closeModalBtn = document.getElementById('close-betting-modal');
        const loginBtn = document.getElementById('login-btn');
        const placeBetBtn = document.getElementById('place-bet-btn');
        const exportBtn = document.getElementById('export-data-btn');
        const clearBtn = document.getElementById('clear-history-btn');
        const forgotPwdBtn = document.getElementById('forgot-password-btn');
        
        if (bettingBtn) {
            bettingBtn.addEventListener('click', () => {
                modal.style.display = 'flex';
                if (game.currentUser) {
                    document.getElementById('login-section').style.display = 'none';
                    document.getElementById('user-section').style.display = 'block';
                    game.updateUI();
                } else {
                    document.getElementById('login-section').style.display = 'block';
                    document.getElementById('user-section').style.display = 'none';
                    document.getElementById('login-username').value = '';
                    document.getElementById('login-password').value = '';
                    document.getElementById('login-email').value = '';
                }
            });
        }
        if (closeModalBtn) closeModalBtn.addEventListener('click', () => modal.style.display = 'none');
        if (modal) modal.addEventListener('click', (e) => { if (e.target === modal) modal.style.display = 'none'; });
        
        if (loginBtn) {
            loginBtn.addEventListener('click', () => {
                const username = document.getElementById('login-username').value.trim();
                const password = document.getElementById('login-password').value;
                const email = document.getElementById('login-email').value.trim();
                const remember = document.getElementById('remember-checkbox').checked;
                if (!username || !password) {
                    alert('请输入用户名和密码');
                    return;
                }
                let user = game.users[username];
                if (!user) {
                    user = game.register(username, password, email);
                    if (!user) {
                        alert('注册失败');
                        return;
                    }
                } else if (user.password !== password) {
                    alert('密码错误');
                    return;
                }
                const logged = game.login(username, password, remember);
                if (logged) {
                    document.getElementById('login-section').style.display = 'none';
                    document.getElementById('user-section').style.display = 'block';
                    game.updateUI();
                } else {
                    alert('登录失败');
                }
            });
        }
        
        if (placeBetBtn) {
            placeBetBtn.addEventListener('click', async () => {
                if (!game.currentUser) {
                    alert('请先登录');
                    return;
                }
                const company = document.getElementById('bet-company').value;
                const betType = document.getElementById('bet-type').value;
                const amount = parseFloat(document.getElementById('bet-amount').value);
                const numbers = document.getElementById('bet-number').value.trim();
                
                let drawDate = window.selectedDate || (window.availableDates && window.availableDates[0]) || new Date().toISOString().slice(0,10);
                const url = `data/${drawDate}/${company}.json?t=${Date.now()}`;
                let drawResult = null;
                try {
                    const res = await fetch(url);
                    if (res.ok) drawResult = await res.json();
                } catch(e) {}
                
                const result = game.placeBet(company, betType, amount, numbers, drawResult);
                if (result.success) {
                    game.updateUI();
                    let msg = `下注 ${amount} RM，号码 ${numbers}`;
                    if (result.prize > 0) {
                        msg += ` 🎉 中奖 ${result.prizeName} +${result.prize} RM！`;
                    } else {
                        msg += ` ❌ 未中奖`;
                    }
                    alert(msg);
                    document.getElementById('bet-number').value = '';
                } else {
                    alert(result.message);
                }
            });
        }
        
        if (exportBtn) exportBtn.addEventListener('click', () => game.exportData());
        if (clearBtn) clearBtn.addEventListener('click', () => game.clearHistory());
        
        if (forgotPwdBtn) {
            forgotPwdBtn.addEventListener('click', () => {
                const username = prompt('请输入用户名');
                const email = prompt('请输入注册邮箱');
                if (!username || !email) return;
                const user = game.users[username];
                if (user && user.email === email) {
                    const newPwd = prompt('请输入新密码');
                    if (newPwd) {
                        user.password = newPwd;
                        game.saveUsers();
                        alert('密码已重置，请重新登录');
                    }
                } else {
                    alert('用户名或邮箱不匹配');
                }
            });
        }
    });
    
    window.bettingGame = game;
})();