// ==================== 初始化启动 ====================
document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('click', e => {
        const el = e.target.closest('[data-action]');
        if (!el) return;
        switch (el.dataset.action) {
            case 'toggleDate': toggleDateDropdown(); break;
            case 'refresh': forceRefresh(); break;
            case 'modal': openModal(el.dataset.modal); break;
            case 'close': closeModal(el.dataset.modal); break;
            case 'dark': toggleDarkMode(); break;
        }
    });

    initCalendar();

    if (localStorage.getItem('darkMode')==='enabled') {
        document.body.classList.add('dark-mode');
        document.getElementById('dark-mode-btn').innerHTML = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>';
    }

    document.querySelectorAll('.modal-overlay').forEach(o => o.addEventListener('click', e => { if(e.target===e.currentTarget) o.style.display='none'; }));

    loadDateIndex();
});
