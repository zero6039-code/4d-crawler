/* docs/js/lucky.js — 777 老虎机式 Lucky Number */
document.addEventListener('DOMContentLoaded', () => {
    const boxes = [1, 2, 3, 4].map(i => document.getElementById('digit' + i));
    const spinBtn = document.getElementById('spin-btn');
    const modal = document.getElementById('lucky-modal');
    if (!boxes.every(Boolean) || !spinBtn || !modal) return;

    const ROUNDS = 4;
    let rafIds = [];
    let running = false;

    boxes.forEach(box => {
        box.textContent = '';
        const reel = document.createElement('div');
        reel.className = 'lucky-reel';
        box.appendChild(reel);
    });

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function buildCells(target) {
        const cells = [target];
        for (let r = 0; r < ROUNDS; r++)
            for (let d = 0; d < 10; d++) cells.push(d);
        return cells;
    }

    function cancelSpin() {
        rafIds.forEach(id => cancelAnimationFrame(id));
        rafIds = [];
        boxes.forEach(b => b.classList.remove('stopped'));
        running = false;
        spinBtn.disabled = false;
    }

    spinBtn.addEventListener('click', () => {
        if (running) return;
        if (reduceMotion) {
            boxes.forEach(b => {
                b.querySelector('.lucky-reel').innerHTML = '<div class="lucky-cell">' + Math.floor(Math.random() * 10) + '</div>';
            });
            return;
        }

        running = true;
        spinBtn.disabled = true;
        rafIds = [];

        boxes.forEach((box, i) => {
            box.classList.remove('stopped');
            const reel = box.querySelector('.lucky-reel');
            const h = box.clientHeight || 104;
            const target = Math.floor(Math.random() * 10);
            const cells = buildCells(target);
            const distance = (cells.length - 1) * h;
            reel.innerHTML = cells.map(d => '<div class="lucky-cell">' + d + '</div>').join('');
            reel.style.transform = 'translateY(' + (-distance) + 'px)';

            const duration = 1500 + i * 420;
            let start = null;
            const step = ts => {
                if (modal.style.display === 'none') { cancelSpin(); return; }
                if (start === null) start = ts;
                const t = Math.min((ts - start) / duration, 1);
                const eased = 1 - Math.pow(1 - t, 4);
                reel.style.transform = 'translateY(' + (-distance * (1 - eased)) + 'px)';
                if (t < 1) {
                    rafIds[i] = requestAnimationFrame(step);
                } else {
                    reel.style.transform = 'translateY(0px)';
                    box.classList.add('stopped');
                    if (i === boxes.length - 1) { running = false; spinBtn.disabled = false; }
                }
            };
            rafIds[i] = requestAnimationFrame(step);
        });
    });
});
