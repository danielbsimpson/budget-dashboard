/* tab-next.js – Next Month tab */

function renderTabNext() {
  const today    = new Date();
  const nm       = new Date(today.getFullYear(), today.getMonth() + 1, 1);
  const year     = nm.getFullYear();
  const month    = nm.getMonth();
  const mName    = nm.toLocaleDateString('en-US', { month: 'long' });

  const nmOpening = S._cm_projected_eom || 0;

  /* Build recurring amounts/days (sidebar defaults + overrides) */
  const recAmts = {}, recDays = {};
  for (const key of Object.keys(REC_DEFAULTS)) {
    recAmts[key] = S.nm_overrides[key]     !== undefined ? S.nm_overrides[key]     : S[key].amount;
    recDays[key] = S.nm_day_overrides[key] !== undefined ? S.nm_day_overrides[key] : S[key].day;
  }

  const expenses = buildExpensesNext(year, month, recAmts, recDays);
  const rows     = buildLedger(year, month, expenses, nmOpening);

  /* Summary */
  const totalIncome   = expenses.reduce((s, e) => e.amount < 0 ? s + Math.abs(e.amount) : s, 0);
  const totalExpenses = expenses.reduce((s, e) => e.amount > 0 ? s + e.amount : s, 0);
  const eomBalance    = rows.length ? rows[rows.length - 1].runningBalance : nmOpening;

  /* Expense pie data */
  const catMap = {};
  for (const e of expenses) {
    if (e.amount > 0) catMap[e.category] = (catMap[e.category] || 0) + e.amount;
  }
  const pieLabels = Object.keys(catMap);
  const pieData   = pieLabels.map(k => parseFloat(catMap[k].toFixed(2)));
  const PIE_COLORS = ['#4f8ef7','#e74c3c','#2ecc71','#f39c12','#9b59b6','#1abc9c','#e67e22'];

  /* Override expander content */
  const overrideablKeys = ['rec_gas','rec_elec','rec_water','rec_sewer','rec_internet',
                            'rec_phone','rec_student','rec_insurance','rec_subs'];
  const overrideRows = overrideablKeys.map(key => `
    <div class="col2" style="margin-bottom:8px">
      <div class="field">
        <label>${REC_DEFAULTS[key].label} ($)</label>
        <input type="number" class="nm-ov-amt" data-key="${key}"
               value="${recAmts[key].toFixed(2)}" min="0" step="0.01">
      </div>
      <div class="field" style="width:72px">
        <label>Day</label>
        <input type="number" class="nm-ov-day" data-key="${key}"
               value="${recDays[key]}" min="1" max="31" step="1">
      </div>
    </div>`).join('');

  /* One-off rows */
  const oneOffRows = S.nm_oe_rows.map((r, i) => `
    <div class="oe-row">
      <div>
        <label>Description</label>
        <input type="text" class="nm-oe-desc" data-idx="${i}" value="${_esc(r.description || '')}" placeholder="e.g. Netflix annual">
      </div>
      <div>
        <label>Amount ($)</label>
        <input type="number" class="nm-oe-amt" data-idx="${i}" value="${(r.amount || 0).toFixed(2)}" min="0" step="0.01">
      </div>
      <div>
        <label>Day</label>
        <input type="number" class="nm-oe-day" data-idx="${i}" value="${r.day || 1}" min="1" max="31" step="1">
      </div>
      <div style="display:flex;align-items:flex-end">
        <button class="btn btn-sm btn-danger nm-oe-del" data-idx="${i}" style="margin-bottom:0">🗑</button>
      </div>
    </div>`).join('');

  const eomColor = eomBalance > 0 ? 'tile-green' : 'tile-red';
  const incomeColor = 'tile-green', expColor = 'tile-red';

  const panel = document.getElementById('panel-next');
  panel.innerHTML = `
    <div class="tab-content">
      <h2>🗓️ ${mName} ${year} Budget</h2>

      <div class="info-banner">
        📌 Opening balance: <strong>${fmt(nmOpening)}</strong>
        — carried from end-of-${today.toLocaleDateString('en-US',{month:'long'})} projection.
        Recurring bills and income are pulled from sidebar settings.
      </div>

      <div class="main-expander" id="nm-exp-ov">
        <button class="main-expander-toggle" onclick="_toggleMainExpander('nm-exp-ov')">
          <span>🔧 Override amounts &amp; due dates for this month (optional)</span>
          <i class="chevron">›</i>
        </button>
        <div class="main-expander-body">
          <p class="caption" style="margin-bottom:12px">Changes here only affect the next-month forecast, not sidebar defaults.</p>
          ${overrideRows}
          <button class="btn btn-sm" id="nm-ov-reset">↩ Reset to sidebar values</button>
        </div>
      </div>

      <div class="main-expander" id="nm-exp-oe">
        <button class="main-expander-toggle" onclick="_toggleMainExpander('nm-exp-oe')">
          <span>📋 Additional one-off expenses (optional)</span>
          <i class="chevron">›</i>
        </button>
        <div class="main-expander-body">
          <p class="caption" style="margin-bottom:10px">Extra or irregular expenses for next month only.</p>
          <div id="nm-oe-list">${oneOffRows}</div>
          <button class="btn btn-sm add-row-btn" id="nm-oe-add">➕ Add Expense</button>
        </div>
      </div>

      <h3>📊 Next Month Summary</h3>
      <div class="tiles">
        ${_tile('Opening Balance',  fmt(nmOpening),     'from this month EOM',         'tile-blue')}
        ${_tile('Total Income',     fmt(totalIncome),   'projected paychecks',          incomeColor)}
        ${_tile('Total Expenses',   fmt(totalExpenses), 'bills + recurring + one-offs', expColor)}
        ${_tile('Projected EOM',    fmt(eomBalance),    'end of next month',            eomColor)}
      </div>

      <div class="chart-wrapper">
        <canvas id="chart-next-bal"></canvas>
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px">
        <div class="chart-wrapper" style="height:260px">
          <canvas id="chart-next-pie"></canvas>
        </div>
        <div>
          <h4>Expense Breakdown</h4>
          ${_expenseBreakdownTable(catMap)}
        </div>
      </div>

      <h3>📒 Next Month Ledger</h3>
      <div class="table-wrapper">
        ${_buildNextLedgerTable(rows)}
      </div>
    </div>`;

  /* Bind override inputs */
  panel.querySelectorAll('.nm-ov-amt').forEach(el => el.addEventListener('change', () => {
    S.nm_overrides[el.dataset.key] = parseFloat(el.value) || 0; scheduleRerender();
  }));
  panel.querySelectorAll('.nm-ov-day').forEach(el => el.addEventListener('change', () => {
    S.nm_day_overrides[el.dataset.key] = parseInt(el.value) || 1; scheduleRerender();
  }));

  const resetOv = document.getElementById('nm-ov-reset');
  if (resetOv) resetOv.addEventListener('click', () => {
    S.nm_overrides = {}; S.nm_day_overrides = {}; scheduleRerender();
  });

  /* One-off binding */
  panel.querySelectorAll('.nm-oe-desc').forEach(el => el.addEventListener('input', () => {
    S.nm_oe_rows[+el.dataset.idx].description = el.value; scheduleRerender();
  }));
  panel.querySelectorAll('.nm-oe-amt').forEach(el => el.addEventListener('change', () => {
    S.nm_oe_rows[+el.dataset.idx].amount = parseFloat(el.value) || 0; scheduleRerender();
  }));
  panel.querySelectorAll('.nm-oe-day').forEach(el => el.addEventListener('change', () => {
    S.nm_oe_rows[+el.dataset.idx].day = parseInt(el.value) || 1; scheduleRerender();
  }));
  panel.querySelectorAll('.nm-oe-del').forEach(el => el.addEventListener('click', () => {
    S.nm_oe_rows.splice(+el.dataset.idx, 1); scheduleRerender();
  }));
  const addOE = document.getElementById('nm-oe-add');
  if (addOE) addOE.addEventListener('click', () => {
    S.nm_oe_rows.push({ description: '', amount: 0, day: 1 }); scheduleRerender();
  });

  /* Charts */
  _drawNextBalChart(rows, mName + ' ' + year);
  _drawNextPieChart(pieLabels, pieData, PIE_COLORS);
}

function _drawNextBalChart(rows, title) {
  const labels = rows.map(r => r.date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
  const data   = rows.map(r => parseFloat(r.runningBalance.toFixed(2)));
  createLineChart('chart-next-bal', [
    {
      label:           'Projected Balance',
      data,
      borderColor:     '#4f8ef7',
      backgroundColor: 'rgba(79,142,247,0.1)',
      fill:            true,
      pointRadius:     2,
      borderWidth:     2,
    },
  ], labels, {
    plugins: {
      title: { display: true, text: `Balance — ${title}`, color: '#ccc', font: { size: 13 } },
      tooltip: { callbacks: { label: ctx => ` Balance: ${fmt(ctx.raw)}` } },
    },
  });
}

function _drawNextPieChart(labels, data, colors) {
  createPieChart('chart-next-pie', labels, data, colors);
}

function _expenseBreakdownTable(catMap) {
  const total = Object.values(catMap).reduce((s, v) => s + v, 0);
  let html = `<table style="font-size:0.8rem">
    <thead><tr><th>Category</th><th style="text-align:right">Amount</th><th style="text-align:right">%</th></tr></thead>
    <tbody>`;
  for (const [cat, amt] of Object.entries(catMap).sort((a,b) => b[1]-a[1])) {
    const pct = total > 0 ? (amt / total * 100).toFixed(1) : '0.0';
    html += `<tr><td>${cat}</td><td style="text-align:right" class="amt-red">${fmt(amt)}</td>
             <td style="text-align:right;color:var(--text-dim)">${pct}%</td></tr>`;
  }
  html += `<tr style="font-weight:700"><td>Total</td><td style="text-align:right">${fmt(total)}</td><td></td></tr>`;
  html += '</tbody></table>';
  return html;
}

function _buildNextLedgerTable(rows) {
  let html = `
    <table>
      <thead><tr>
        <th>Date</th>
        <th>Description</th>
        <th>Net</th>
        <th>Running Balance</th>
      </tr></thead>
      <tbody>`;

  for (const row of rows) {
    if (!row.hasActivity) continue;
    const dateStr = row.date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
    const amtCls  = row.amount < 0 ? 'amt-green' : row.amount > 0 ? 'amt-red' : '';
    const balCls  = row.runningBalance < 0 ? 'amt-red' : 'amt-green';
    html += `
  <tr>
    <td>${dateStr}</td>
    <td>${row.description}</td>
    <td class="${amtCls}">${row.amount !== 0 ? fmt(row.amount) : '—'}</td>
    <td class="${balCls}">${fmt(row.runningBalance)}</td>
  </tr>`;
  }
  html += '</tbody></table>';
  return html;
}

/* Shared */
function _toggleMainExpander(id) {
  const el   = document.getElementById(id);
  if (!el) return;
  const btn  = el.querySelector('.main-expander-toggle');
  const body = el.querySelector('.main-expander-body');
  btn.classList.toggle('open');
  body.classList.toggle('open');
}

