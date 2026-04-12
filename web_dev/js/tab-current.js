/* tab-current.js – Current Month tab */

function renderTabCurrent() {
  const today  = new Date();
  const year   = today.getFullYear();
  const month  = today.getMonth();     // 0-indexed
  const mName  = today.toLocaleDateString('en-US', { month: 'long' });

  /* Build data */
  const expenses     = buildExpensesCurrent(year, month);
  const rows         = buildLedger(year, month, expenses, S.cm_opening);
  const projectedEOM = addActualColumn(rows, S.cm_current_bal, today);

  /* Persist EOM projection for Tab 2 */
  S._cm_projected_eom = projectedEOM;

  /* Summary numbers */
  const totalIncome   = expenses.reduce((s, e) => e.amount < 0 ? s + Math.abs(e.amount) : s, 0);
  const totalExpenses = expenses.reduce((s, e) => e.amount > 0 ? s + e.amount : s, 0);
  const todayRow      = rows.find(r => _sameDay(r.date, today));
  const projToday     = todayRow ? todayRow.runningBalance : null;
  const variance      = projToday !== null ? S.cm_current_bal - projToday : 0;

  /* Tile colours */
  const RENT_THRESHOLD = S.rec_rent.amount;
  const obDiff  = S.cm_opening - RENT_THRESHOLD;
  const obColor = obDiff > 100 ? 'tile-green' : obDiff >= -100 ? 'tile-yellow' : 'tile-red';
  const cbColor = projectedEOM <= 0 ? 'tile-red' : projectedEOM <= 100 ? 'tile-yellow' : 'tile-green';
  const ptColor = projToday === null ? 'tile-green' : projToday > S.cm_current_bal ? 'tile-red' : 'tile-green';

  const nextRentTotal = S.rec_rent.amount + S.rec_parking.amount + S.rec_water.amount + S.rec_sewer.amount;
  const peDiff  = projectedEOM - nextRentTotal;
  const peColor = peDiff > 100 ? 'tile-green' : peDiff >= -100 ? 'tile-yellow' : 'tile-red';

  const varSign = variance >= 0 ? '+' : '-';
  const ptSub   = projToday !== null
    ? `${varSign}$${Math.abs(variance).toFixed(2)} vs projected`
    : '—';

  const panel = document.getElementById('panel-current');
  panel.innerHTML = `
    <div class="tab-content">
      <h2>📅 ${mName} ${year} Budget</h2>

      <div class="input-row">
        <div class="input-group">
          <label for="cm-opening">Opening Checking Balance ($)</label>
          <input type="number" id="cm-opening" value="${S.cm_opening.toFixed(2)}" step="0.01">
          <small>Your balance at the start of the month (day 1).</small>
        </div>
        <div class="input-group">
          <label for="cm-current">Current Checking Balance ($)</label>
          <input type="number" id="cm-current" value="${S.cm_current_bal.toFixed(2)}" step="0.01">
          <small>Your actual balance right now — projects the rest of the month from today.</small>
        </div>
      </div>

      <div class="chart-wrapper">
        <canvas id="chart-current-bal"></canvas>
      </div>

      <h3>📊 Month Summary</h3>
      <div class="tiles">
        ${_tile('Opening Balance',    fmt(S.cm_opening),      `${obDiff >= 0 ? '+' : ''}$${Math.abs(obDiff).toFixed(2)} vs rent threshold`, obColor)}
        ${_tile('Current Balance',    fmt(S.cm_current_bal),  `Projected EOM: ${fmt(projectedEOM)}`,                                        cbColor)}
        ${_tile('Projected Today',    projToday !== null ? fmt(projToday) : '—', ptSub,                                                      ptColor)}
        ${_tile('Total Income',       fmt(totalIncome),        'this month',                                                                   'tile-green')}
        ${_tile('Total Expenses',     fmt(totalExpenses),      'this month',                                                                   'tile-red')}
        ${_tile('Projected EOM',      fmt(projectedEOM),       `${peDiff >= 0 ? '+' : ''}$${Math.abs(peDiff).toFixed(2)} vs next rent`,      peColor)}
      </div>

      <h3>📒 Daily Ledger</h3>
      <div class="table-wrapper">
        ${_buildLedgerTable(rows, today)}
      </div>
    </div>`;

  /* Bind inputs */
  document.getElementById('cm-opening').addEventListener('change', e => {
    S.cm_opening = parseFloat(e.target.value) || 0;
    scheduleRerender();
  });
  document.getElementById('cm-current').addEventListener('change', e => {
    S.cm_current_bal = parseFloat(e.target.value) || 0;
    scheduleRerender();
  });

  /* Draw chart */
  _drawCurrentBalanceChart(rows, today, `${mName} ${year}`);
}

/* ── Chart ───────────────────────────────────────────────────────────────── */
function _drawCurrentBalanceChart(rows, today, title) {
  const labels    = rows.map(r => r.date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
  const projected = rows.map(r => parseFloat(r.runningBalance.toFixed(2)));
  const actual    = rows.map(r =>
    r.actualBalance !== null && r.actualBalance !== undefined
      ? parseFloat(r.actualBalance.toFixed(2))
      : null,
  );

  /* Find today index for annotation */
  const todayIdx = rows.findIndex(r => _sameDay(r.date, today));

  createLineChart('chart-current-bal', [
    {
      label:           'Projected (from opening)',
      data:            projected,
      borderColor:     'rgba(150,150,150,0.7)',
      backgroundColor: 'transparent',
      borderDash:      [5, 5],
      pointRadius:     2,
      borderWidth:     1.5,
    },
    {
      label:           'Actual / Forward Projection',
      data:            actual,
      borderColor:     '#4f8ef7',
      backgroundColor: 'rgba(79,142,247,0.08)',
      fill:            true,
      pointRadius:     3,
      borderWidth:     2.5,
      spanGaps:        false,
    },
  ], labels, {
    plugins: {
      title: { display: true, text: `Checking — ${title}`, color: '#ccc', font: { size: 13 } },
      tooltip: {
        callbacks: {
          label: ctx => ` ${ctx.dataset.label}: ${ctx.raw !== null ? fmt(ctx.raw) : '—'}`,
        },
      },
    },
  });
}

/* ── Ledger table ────────────────────────────────────────────────────────── */
function _buildLedgerTable(rows, today) {
  const active = rows.filter(r => r.hasActivity);
  if (!active.length) return '<p class="caption">No transactions this month.</p>';

  let html = `
    <table>
      <thead><tr>
        <th>Date</th>
        <th>Description</th>
        <th>Net</th>
        <th>Balance (Proj.)</th>
        <th>Balance (Actual)</th>
      </tr></thead>
      <tbody>`;

  for (const row of active) {
    const isToday   = _sameDay(row.date, today);
    const dateStr   = row.date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
    const amtCls    = row.amount < 0 ? 'amt-green' : row.amount > 0 ? 'amt-red' : '';
    const balCls    = row.runningBalance < 0 ? 'amt-red' : 'amt-green';
    const hasActual = row.actualBalance !== null && row.actualBalance !== undefined;
    const actStr    = hasActual ? fmt(row.actualBalance) : '—';
    const actCls    = hasActual ? (row.actualBalance < 0 ? 'amt-red' : 'amt-green') : 'amt-gray';

    html += `
  <tr class="${isToday ? 'tr-today' : ''}">
    <td>${dateStr}${isToday ? ' <span class="today-badge">Today</span>' : ''}</td>
    <td>${row.description}</td>
    <td class="${amtCls}">${row.amount !== 0 ? fmt(row.amount) : '—'}</td>
    <td class="${balCls}">${fmt(row.runningBalance)}</td>
    <td class="${actCls}">${actStr}</td>
  </tr>`;
  }

  html += '</tbody></table>';
  return html;
}

/* ── Shared helpers ──────────────────────────────────────────────────────── */
function _tile(label, value, subtitle, colorClass) {
  return `
  <div class="tile ${colorClass}">
    <div class="tile-label">${label}</div>
    <div class="tile-value">${value}</div>
    <div class="tile-sub">${subtitle}</div>
  </div>`;
}

function _sameDay(a, b) {
  return a.getFullYear() === b.getFullYear() &&
         a.getMonth()    === b.getMonth()    &&
         a.getDate()     === b.getDate();
}
