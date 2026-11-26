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

    let html = `<div class="calendar-header"><button class="calendar-nav" data-cal-delta="-1">‹</button><span>${monthNames[month]} ${year}</span><button class="calendar-nav" data-cal-delta="1">›</button></div><table class="calendar-table"><thead><tr><th>Su</th><th>Mo</th><th>Tu</th><th>We</th><th>Th</th><th>Fr</th><th>Sa</th></tr></thead><tbody>`;

    let day = 1;
    for (let i=0; i<6; i++) {
        html += '<tr>';
        for(let j=0; j<7; j++){
            if(i===0&&j<firstDay){html+='<td></td>';}
            else if(day>daysInMonth){html+='<td></td>';}
            else {
                const dateStr = `${year}-${String(month+1).padStart(2,'0')}-${String(day).padStart(2,'0')}`;
                const has = availableDatesSet.has(dateStr), sel = dateStr===selectedDate;
                html += `<td class="${has?'has-data':''} ${sel?'selected':''}" data-cal-date="${dateStr}">${day}</td>`;
                day++;
            }
        }
        html += '</tr>';
        if(day>daysInMonth) break;
    }
    popup.innerHTML = html + `</tbody></table>`;
    if (!calendarBound) {
        calendarBound = true;
        popup.addEventListener('click', e => {
            const nav = e.target.closest('[data-cal-delta]');
            if (nav) { changeCalendarMonth(Number(nav.dataset.calDelta), e); return; }
            const cell = e.target.closest('[data-cal-date]');
            if (cell) selectDateFromCalendar(cell.dataset.calDate, e);
        });
    }
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

