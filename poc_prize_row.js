const fs = require('fs');
const vm = require('vm');
const code = fs.readFileSync('docs/js/main.js', 'utf8');
const grid = { innerHTML: '' };
const el = {
  style: {}, innerHTML: '', innerText: '',
  classList: { toggle(){}, contains(){return false}, add(){} },
  querySelector(){ return { outerHTML: '' }; },
  addEventListener(){}, contains(){ return false; }
};
const sandbox = {
  console,
  localStorage: { getItem(){ return null; }, setItem(){} },
  document: {
    head: { appendChild(){} },
    body: { classList: { toggle(){}, contains(){return false}, add(){} } },
    createElement(){ return { textContent: '', style: {} }; },
    addEventListener(){},
    getElementById(id){ return id === 'companies-grid' ? grid : el; },
    querySelectorAll(){ return []; }
  }
};
sandbox.window = sandbox;
vm.createContext(sandbox);
vm.runInContext(code, sandbox);

const base = {
  draw_date: '23-11-2026',
  draw_no: '4237',
  winning_numbers: ['25','27','37','43','47','49','17'],
  prize_table: [
    ['Group 1','-','-'],
    ['Group 2','$85,299','3'],
    ['Group 3','$1,852','95'],
    ['Group 4','$321','299'],
    ['Group 5','$50','4,311'],
    ['Group 6','$25','7,176'],
    ['Group 7','$10','79,493']
  ],
  prize: '$1,215,505'
};

const R = [];
function ck(n, ok, x='') { R.push([n, ok]); console.log(ok ? 'PASS' : 'FAIL', n, x); }

sandbox.renderCompanies({ singapore_toto: base });
let h = grid.innerHTML;
ck('渲染 Prize 文本', h.includes('Prize: ' + base.prize), base.prize);
ck('使用 toto-prize-row', h.includes('class="toto-prize-row"'));
ck('colspan=3', h.includes('colspan="3"'));
ck('位于 Group 7 之后', h.indexOf('Group 7') >= 0 && h.indexOf('Group 7') < h.indexOf('Prize: ' + base.prize));
ck('只渲染一行', (h.match(/toto-prize-row/g) || []).length === 1);

const old = { ...base }; delete old.prize;
grid.innerHTML = '';
sandbox.renderCompanies({ singapore_toto: old });
ck('旧数据无空行', !grid.innerHTML.includes('Prize:') && !grid.innerHTML.includes('toto-prize-row'));

ck('守卫存在', code.includes("if (cd.prize && typeof cd.prize === 'string'"));
ck('CSS 存在', code.includes('.toto-prize-row td'));

const bad = R.filter(x => !x[1]).map(x => x[0]);
console.log('\nRESULT:', bad.length ? 'FAILED → ' + bad.join(', ') : 'ALL PASS');
process.exit(bad.length ? 1 : 0);
