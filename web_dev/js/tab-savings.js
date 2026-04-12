/* tab-savings.js – Future Savings tab with 5 sub-tabs */

let _activeSavingsSub = 'savings-overview';

function renderTabSavings() {
  const panel = document.getElementById('panel-savings');

  panel.innerHTML = `
    <div class="tab-content">
      <h2>🏦 Future Savings Plans</h2>
      <div class="sub-tab-nav" id="savings-sub-nav">
        <button class="sub-tab-btn ${_activeSavingsSub==='savings-overview'?'active':''}" data-sub="savings-overview">💰 Savings Overview</button>
        <button class="sub-tab-btn ${_activeSavingsSub==='mortgage'?'active':''}"         data-sub="mortgage">🏠 Mortgage</button>
        <button class="sub-tab-btn ${_activeSavingsSub==='car'?'active':''}"              data-sub="car">🚗 Car Loan</button>
        <button class="sub-tab-btn ${_activeSavingsSub==='k401'?'active':''}"             data-sub="k401">📈 401k</button>
        <button class="sub-tab-btn ${_activeSavingsSub==='student'?'active':''}"          data-sub="student">🎓 Student Loans</button>
      </div>
      <div id="savings-sub-panels">
        <div id="sub-savings-overview" class="sub-panel ${_activeSavingsSub==='savings-overview'?'active':''}"></div>
        <div id="sub-mortgage"         class="sub-panel ${_activeSavingsSub==='mortgage'?'active':''}"></div>
        <div id="sub-car"              class="sub-panel ${_activeSavingsSub==='car'?'active':''}"></div>
        <div id="sub-k401"             class="sub-panel ${_activeSavingsSub==='k401'?'active':''}"></div>
        <div id="sub-student"          class="sub-panel ${_activeSavingsSub==='student'?'active':''}"></div>
      </div>
    </div>`;

  /* Sub-tab switching */
  panel.querySelectorAll('.sub-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      _activeSavingsSub = btn.dataset.sub;
      renderTabSavings();
      _renderActiveSavingsSub();
    });
  });

  _renderActiveSavingsSub();
}

function _renderActiveSavingsSub() {
  switch (_activeSavingsSub) {
    case 'savings-overview': _renderSavingsOverview(); break;
    case 'mortgage':         _renderMortgage();        break;
    case 'car':              _renderCar();             break;
    case 'k401':             _render401k();            break;
    case 'student':          _renderStudent();         break;
  }
}

/* ═══════════════════════════════════════════════════════════════════════════
   Sub-tab 1: Savings Overview
═══════════════════════════════════════════════════════════════════════════ */
function _renderSavingsOverview() {
  const el = document.getElementById('sub-savings-overview');

  const liquid    = S.ally + S.burke + S.rh;
  const totLiquid = liquid + S.sav_checking;
  const totAll    = totLiquid + S.schwab + S.merill;
  const goalBal   = totLiquid + S.schwab;
  const remaining = S.sav_goal - goalBal;
  const progress  = S.sav_goal > 0 ? Math.min(goalBal / S.sav_goal, 1) : 0;
  const pct       = (progress * 100).toFixed(1);

  /* Projection rows */
  const today    = new Date();
  const projRows = [];
  let bal        = liquid;
  for (let i = 1; i <= S.sav_months; i++) {
    const d = new Date(today.getFullYear(), today.getMonth() + i, 1);
    bal += S.monthly_save;
    projRows.push({ label: d.toLocaleDateString('en-US',{month:'short',year:'2-digit'}), bal: parseFloat(bal.toFixed(2)) });
  }

  el.innerHTML = `
    <h3>Current Accounts</h3>
    <div class="savings-grid">
      <div>
        ${_savField('ally',         'Ally Savings ($)')}
        ${_savField('burke',        'Burke Savings ($)')}
        ${_savField('rh',           'Robin Hood ($)')}
        ${_savField('schwab',       'Charles Schwab ($)')}
        ${_savField('merill',       'Merrill (TJX) ($)')}
      </div>
      <div>
        ${_savField('sav_checking', 'Checking ($)')}
        ${_savField('sav_goal',     'Savings Goal ($)', 1000)}
        <br>
        <div class="metrics" style="flex-direction:column;gap:8px">
          ${_metric('Liquid Savings',              fmt(liquid))}
          ${_metric('Total Liquid (+ Checking)',   fmt(totLiquid))}
          ${_metric('Total Combined (all accts)',  fmt(totAll))}
        </div>
      </div>
    </div>

    <h4>Goal Progress — ${fmt(goalBal)} / ${fmt(S.sav_goal)} (${pct}%)</h4>
    <div class="progress-bar-wrapper">
      <div class="progress-bar-fill" style="width:${(progress*100).toFixed(1)}%"></div>
    </div>
    <p class="progress-label">${remaining <= 0 ? '✅ Goal reached!' : fmt(remaining) + ' remaining'}</p>

    <div class="chart-wrapper">
      <canvas id="chart-sav-pie"></canvas>
    </div>

    <h3>Monthly Savings Projection</h3>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px">
      ${_savField('monthly_save', 'Monthly Savings Amount ($)', 50)}
      <div class="input-group">
        <label for="sav-months">Months to project: <strong id="sav-months-val">${S.sav_months}</strong></label>
        <input type="range" id="sav-months" min="6" max="60" step="1" value="${S.sav_months}">
      </div>
    </div>

    <div class="chart-wrapper tall">
      <canvas id="chart-sav-proj"></canvas>
    </div>`;

  /* Bind */
  _bindSavNum(el, 'ally',         v => { S.ally         = v; scheduleRerender('savings'); });
  _bindSavNum(el, 'burke',        v => { S.burke        = v; scheduleRerender('savings'); });
  _bindSavNum(el, 'rh',           v => { S.rh           = v; scheduleRerender('savings'); });
  _bindSavNum(el, 'schwab',       v => { S.schwab       = v; scheduleRerender('savings'); });
  _bindSavNum(el, 'merill',       v => { S.merill       = v; scheduleRerender('savings'); });
  _bindSavNum(el, 'sav_checking', v => { S.sav_checking = v; scheduleRerender('savings'); });
  _bindSavNum(el, 'sav_goal',     v => { S.sav_goal     = v; scheduleRerender('savings'); });
  _bindSavNum(el, 'monthly_save', v => { S.monthly_save = v; scheduleRerender('savings'); });

  const slider = document.getElementById('sav-months');
  if (slider) {
    slider.addEventListener('input', () => {
      S.sav_months = parseInt(slider.value);
      document.getElementById('sav-months-val').textContent = S.sav_months;
      scheduleRerender('savings');
    });
  }

  /* Charts */
  setTimeout(() => {
    createPieChart('chart-sav-pie',
      ['Ally Savings','Burke Savings','Robin Hood','Charles Schwab','Merrill','Checking'],
      [S.ally, S.burke, S.rh, S.schwab, S.merill, S.sav_checking],
      ['#4f8ef7','#2ecc71','#f39c12','#9b59b6','#1abc9c','#e67e22'],
    );

    createLineChart('chart-sav-proj',
      [
        {
          label: 'Projected Liquid Savings',
          data:  projRows.map(r => r.bal),
          borderColor: '#2ecc71',
          backgroundColor: 'rgba(46,204,113,0.1)',
          fill: true,
          pointRadius: 2,
          borderWidth: 2,
        },
        {
          label: `Goal (${fmt(S.sav_goal)})`,
          data:  projRows.map(() => S.sav_goal),
          borderColor: 'rgba(46,204,113,0.55)',
          backgroundColor: 'transparent',
          borderDash: [6, 3],
          pointRadius: 0,
          borderWidth: 2,
        },
      ],
      projRows.map(r => r.label),
      {
        plugins: {
          title: { display: true, text: `Projected Liquid Savings (${S.sav_months} months)`, color:'#ccc' },
        },
      },
    );
  }, 0);
}

/* ═══════════════════════════════════════════════════════════════════════════
   Sub-tab 2: Mortgage
═══════════════════════════════════════════════════════════════════════════ */
function _renderMortgage() {
  const el = document.getElementById('sub-mortgage');

  const dp       = S.hp * S.dp_pct / 100;
  const needed   = Math.max(dp - S.dp_saved, 0);
  const months   = S.dp_monthly > 0 ? Math.ceil(needed / S.dp_monthly) : 999;

  /* Savings progress rows */
  const today   = new Date();
  const saveRows = [];
  let   bal     = S.dp_saved;
  for (let i = 1; i <= months + 2 && i <= 120; i++) {
    const d = new Date(today.getFullYear(), today.getMonth() + i, 1);
    bal = Math.min(bal + S.dp_monthly, dp * 1.1);
    saveRows.push({ label: d.toLocaleDateString('en-US',{month:'short',year:'2-digit'}), saved: parseFloat(bal.toFixed(2)), target: parseFloat(dp.toFixed(2)) });
  }

  /* Down-payment table */
  const prices = [200000,250000,300000,350000,400000,450000,500000,550000,600000];
  const pcts   = [3,5,8,10,12,20];
  const dpTableHtml = `
    <div class="data-table-wrapper">
      <table>
        <thead><tr><th>Home Price</th>${pcts.map(p=>`<th>${p}%</th>`).join('')}</tr></thead>
        <tbody>
          ${prices.map(pr => `<tr><td>${fmt(pr)}</td>${pcts.map(p=>`<td>${fmt(pr*p/100)}</td>`).join('')}</tr>`).join('')}
        </tbody>
      </table>
    </div>`;

  el.innerHTML = `
    <h3>🏠 Mortgage Down Payment Calculator</h3>
    <div class="savings-grid">
      <div>
        ${_savField('hp',         'Home Price ($)',       10000)}
        <div class="input-group" style="margin-bottom:14px">
          <label for="dp-pct-range">Down Payment %: <strong id="dp-pct-val">${S.dp_pct}</strong>%</label>
          <input type="range" id="dp-pct-range" min="3" max="20" step="1" value="${S.dp_pct}">
        </div>
        ${_savField('dp_saved',   'Currently Saved ($)',  500)}
        ${_savField('dp_monthly', 'Monthly Contribution ($)', 50)}
      </div>
      <div>
        <div class="metrics" style="flex-direction:column;gap:8px">
          ${_metric('Required Down Payment', fmt(dp))}
          ${_metric('Already Saved',         fmt(S.dp_saved))}
          ${_metric('Still Needed',           fmt(needed))}
          ${_metric('Months to Goal',         months >= 999 ? '∞' : String(months))}
        </div>
      </div>
    </div>

    <h4>Down Payment Targets by Price &amp; %</h4>
    ${dpTableHtml}

    <div class="chart-wrapper tall">
      <canvas id="chart-dp-savings"></canvas>
    </div>`;

  /* Bind */
  _bindSavNum(el, 'hp',         v => { S.hp         = v; scheduleRerender('savings'); });
  _bindSavNum(el, 'dp_saved',   v => { S.dp_saved   = v; scheduleRerender('savings'); });
  _bindSavNum(el, 'dp_monthly', v => { S.dp_monthly = v; scheduleRerender('savings'); });

  const dpSlider = document.getElementById('dp-pct-range');
  if (dpSlider) {
    dpSlider.addEventListener('input', () => {
      S.dp_pct = parseInt(dpSlider.value);
      document.getElementById('dp-pct-val').textContent = S.dp_pct;
      scheduleRerender('savings');
    });
  }

  setTimeout(() => {
    createLineChart('chart-dp-savings', [
      { label: 'Saved', data: saveRows.map(r=>r.saved), borderColor:'#4f8ef7', backgroundColor:'rgba(79,142,247,0.1)', fill:true, pointRadius:2, borderWidth:2 },
      { label: 'Target', data: saveRows.map(r=>r.target), borderColor:'#2ecc71', borderDash:[5,3], backgroundColor:'transparent', pointRadius:0, borderWidth:2 },
    ], saveRows.map(r=>r.label), {
      plugins: { title: { display:true, text:'Down Payment Savings Progress', color:'#ccc' } },
    });
  }, 0);
}

/* ═══════════════════════════════════════════════════════════════════════════
   Sub-tab 3: Car Loan
═══════════════════════════════════════════════════════════════════════════ */
function _renderCar() {
  const el    = document.getElementById('sub-car');
  const sched = buildCarAmortization();

  const totInterest = sched.reduce((s, r) => s + r.interest, 0);
  const payoffDate  = sched.length ? sched[sched.length-1].date : '—';
  const totalMonths = sched.length;

  /* Limit table display to 60 rows */
  const tableRows = sched.slice(0, 60);

  el.innerHTML = `
    <h3>🚗 Car Loan Amortization</h3>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:16px">
      <div>
        ${_savField('car_bal',   'Current Balance ($)', 100)}
        ${_savField('car_rate',  'Annual Rate (%)',       0.1)}
      </div>
      <div>
        ${_savField('car_pay',   'Monthly Payment ($)',   10)}
        ${_savField('car_extra', 'Extra Annual Pymt Apr ($)', 100)}
      </div>
      <div>
        <div class="input-group" style="margin-bottom:14px">
          <label for="car-start">Loan Start Date</label>
          <input type="date" id="car-start" value="${S.car_start}">
        </div>
        <div class="metrics" style="flex-direction:column;gap:8px;margin-top:8px">
          ${_metric('Total Interest',  fmt(totInterest))}
          ${_metric('Payoff Date',     payoffDate)}
          ${_metric('Total Months',    String(totalMonths))}
        </div>
      </div>
    </div>

    <div class="chart-wrapper">
      <canvas id="chart-car-amort"></canvas>
    </div>
    <div class="chart-wrapper">
      <canvas id="chart-car-bal"></canvas>
    </div>

    <h4>Amortization Schedule (first 60 payments)</h4>
    <div class="data-table-wrapper">
      <table>
        <thead><tr><th>#</th><th>Date</th><th>Payment</th><th>Interest</th><th>Principal</th><th>Balance</th></tr></thead>
        <tbody>
          ${tableRows.map(r => `
            <tr>
              <td>${r.month}</td>
              <td>${r.date}</td>
              <td>${fmt(r.payment)}</td>
              <td class="amt-red">${fmt(r.interest)}</td>
              <td class="amt-green">${fmt(r.principal)}</td>
              <td>${fmt(r.balance)}</td>
            </tr>`).join('')}
        </tbody>
      </table>
    </div>`;

  _bindSavNum(el, 'car_bal',   v => { S.car_bal   = v; scheduleRerender('savings'); });
  _bindSavNum(el, 'car_rate',  v => { S.car_rate  = v; scheduleRerender('savings'); });
  _bindSavNum(el, 'car_pay',   v => { S.car_pay   = v; scheduleRerender('savings'); });
  _bindSavNum(el, 'car_extra', v => { S.car_extra = v; scheduleRerender('savings'); });

  const carStart = document.getElementById('car-start');
  if (carStart) carStart.addEventListener('change', () => { S.car_start = carStart.value; scheduleRerender('savings'); });

  setTimeout(() => {
    /* Stacked bar: principal vs interest */
    createBarChart('chart-car-amort', [
      { label: 'Principal', data: sched.map(r=>r.principal), backgroundColor:'rgba(79,142,247,0.7)', stack:'a' },
      { label: 'Interest',  data: sched.map(r=>r.interest),  backgroundColor:'rgba(231,76,60,0.7)',  stack:'a' },
    ], sched.map(r=>r.date), {
      plugins: { title:{ display:true, text:'Principal vs Interest Per Payment', color:'#ccc' } },
      scales: { x: { stacked:true, ticks:{display:false} }, y:{ stacked:true, ticks:{color:'#8892a4', callback:v=>'$'+v.toLocaleString()} } },
    });

    createLineChart('chart-car-bal', [
      { label:'Remaining Balance', data:sched.map(r=>r.balance), borderColor:'#f39c12', backgroundColor:'rgba(243,156,18,0.1)', fill:true, pointRadius:1.5, borderWidth:2 },
    ], sched.map(r=>r.date), {
      plugins: { title:{ display:true, text:'Remaining Loan Balance', color:'#ccc' } },
      scales: { x:{ ticks:{display:false} }, y:{ ticks:{color:'#8892a4', callback:v=>'$'+v.toLocaleString()} } },
    });
  }, 0);
}

/* ═══════════════════════════════════════════════════════════════════════════
   Sub-tab 4: 401k
═══════════════════════════════════════════════════════════════════════════ */
function _render401k() {
  const el   = document.getElementById('sub-k401');
  const rows = build401kProjection();

  const finalBal = rows.length ? rows[rows.length-1].balance : S.k401_cur;
  const years    = S.k401_retire - S.k401_age;
  const totEmp   = rows.reduce((s,r) => s + r.emp, 0);

  const tableRows = rows.slice(-30);  // last 30 years

  el.innerHTML = `
    <h3>📈 401k Retirement Projections</h3>
    <div class="info-banner">
      IRS limits (2025-2026): Standard $24,500 · Catch-up 50+ $32,500 · Special 60-63 $35,750 · Combined cap $72,000
    </div>
    <div class="savings-grid">
      <div>
        ${_savField('k401_cur',    'Current 401k Balance ($)', 100)}
        ${_savField('k401_sal',    'Current Salary ($)',       1000)}
        <div class="input-group" style="margin-bottom:14px">
          <label for="k401-pct">Employee Contribution %: <strong id="k401-pct-val">${S.k401_pct}</strong>%</label>
          <input type="range" id="k401-pct" min="1" max="30" step="1" value="${S.k401_pct}">
        </div>
        <div class="input-group" style="margin-bottom:14px">
          <label for="k401-emp">Employer Match %: <strong id="k401-emp-val">${S.k401_emp}</strong>%</label>
          <input type="range" id="k401-emp" min="0" max="10" step="1" value="${S.k401_emp}">
        </div>
      </div>
      <div>
        <div class="input-group" style="margin-bottom:14px">
          <label for="k401-growth">Annual Growth Rate %: <strong id="k401-growth-val">${S.k401_growth}</strong>%</label>
          <input type="range" id="k401-growth" min="0" max="15" step="1" value="${S.k401_growth}">
        </div>
        ${_savField('k401_bonus',  'Annual Bonus Contribution ($)', 500)}
        ${_savField('k401_age',    'Current Age', 1)}
        ${_savField('k401_retire', 'Target Retirement Age', 1)}
      </div>
    </div>

    <div class="metrics">
      ${_metric('Projected Balance at Retirement', fmt(finalBal))}
      ${_metric('Years to Retirement',             String(years))}
      ${_metric('Total Employee Contributions',    fmt(totEmp))}
    </div>

    <div class="chart-wrapper tall">
      <canvas id="chart-k401-growth"></canvas>
    </div>
    <div class="chart-wrapper tall">
      <canvas id="chart-k401-contrib"></canvas>
    </div>

    <h4>Annual Contribution Detail (last 30 years)</h4>
    <div class="data-table-wrapper">
      <table>
        <thead><tr><th>Year</th><th>Age</th><th>Emp. Contrib.</th><th>Employer Match</th><th>Bonus</th><th>IRS Limit</th><th>EoY Balance</th></tr></thead>
        <tbody>
          ${tableRows.map(r => `
            <tr>
              <td>${r.year}</td>
              <td>${r.age}</td>
              <td>${fmt(r.emp)}</td>
              <td class="amt-green">${fmt(r.er)}</td>
              <td>${fmt(r.bonus)}</td>
              <td class="amt-gray">${fmt(r.cap)}</td>
              <td class="amt-green"><strong>${fmt(r.balance)}</strong></td>
            </tr>`).join('')}
        </tbody>
      </table>
    </div>`;

  /* Bind */
  _bindSavNum(el, 'k401_cur',    v => { S.k401_cur    = v; scheduleRerender('savings'); });
  _bindSavNum(el, 'k401_sal',    v => { S.k401_sal    = v; scheduleRerender('savings'); });
  _bindSavNum(el, 'k401_bonus',  v => { S.k401_bonus  = v; scheduleRerender('savings'); });
  _bindSavNum(el, 'k401_age',    v => { S.k401_age    = parseInt(v)||36; scheduleRerender('savings'); });
  _bindSavNum(el, 'k401_retire', v => { S.k401_retire = parseInt(v)||65; scheduleRerender('savings'); });

  _bindSlider('k401-pct',    'k401-pct-val',    v => { S.k401_pct    = v; });
  _bindSlider('k401-emp',    'k401-emp-val',    v => { S.k401_emp    = v; });
  _bindSlider('k401-growth', 'k401-growth-val', v => { S.k401_growth = v; });

  setTimeout(() => {
    createAreaChart('chart-k401-growth', [
      { label: 'Balance', data: rows.map(r=>r.balance), borderColor:'#4f8ef7', backgroundColor:'rgba(79,142,247,0.15)', pointRadius:1.5, borderWidth:2 },
    ], rows.map(r=>'Age '+r.age), {
      plugins: { title:{ display:true, text:`Projected 401k Growth to Age ${S.k401_retire}`, color:'#ccc' } },
    });

    createBarChart('chart-k401-contrib', [
      { label:'Employee',       data:rows.map(r=>r.emp),   backgroundColor:'rgba(79,142,247,0.8)',  stack:'a' },
      { label:'Employer Match', data:rows.map(r=>r.er),    backgroundColor:'rgba(46,204,113,0.8)',  stack:'a' },
      { label:'Bonus',          data:rows.map(r=>r.bonus), backgroundColor:'rgba(243,156,18,0.8)',  stack:'a' },
      { label:'IRS Limit',      data:rows.map(r=>r.cap),   borderColor:'#e74c3c', backgroundColor:'transparent', type:'line', borderWidth:2, borderDash:[4,3], pointRadius:0 },
    ], rows.map(r=>''+r.age), {
      plugins: { title:{ display:true, text:'Annual Contributions by Age', color:'#ccc' } },
      scales: { x:{ stacked:true }, y:{ stacked:true, ticks:{color:'#8892a4', callback:v=>'$'+v.toLocaleString()} } },
    });
  }, 0);
}

/* ═══════════════════════════════════════════════════════════════════════════
   Sub-tab 5: Student Loans
═══════════════════════════════════════════════════════════════════════════ */
function _renderStudent() {
  const el       = document.getElementById('sub-student');
  const totalPmt = S.rec_student.amount || 423;
  const pay2     = Math.max(totalPmt - S.sl_pay1, 0);
  const sched    = buildStudentLoanSchedule();

  const loan1Done = sched.find(r => r.b1 === 0);
  const loan2Done = sched[sched.length - 1];
  const totI1     = sched.reduce((s,r)=>s+r.i1,0);
  const totI2     = sched.reduce((s,r)=>s+r.i2,0);

  el.innerHTML = `
    <h3>🎓 Student Loan Payoff Planner</h3>
    <div class="info-banner">
      💳 Total monthly payment: <strong>${fmt(totalPmt)}</strong>
      (from Sidebar → Bills → Student Loans).
      Split below between Loan 1 and Loan 2.
    </div>

    <div class="savings-grid">
      <div>
        <h4>Loan 1 — Direct Grad PLUS</h4>
        ${_savField('sl_bal1',  'Current Balance ($)',  10)}
        ${_savField('sl_rate1', 'Annual Interest Rate (%)', 0.01)}
        <div class="input-group" style="margin-bottom:14px">
          <label for="sl-pay1">Monthly Payment → Loan 1: <strong id="sl-pay1-val">${fmt(S.sl_pay1)}</strong></label>
          <input type="range" id="sl-pay1" min="0" max="${totalPmt.toFixed(0)}" step="1" value="${S.sl_pay1.toFixed(0)}">
          <small>Remainder (${fmt(pay2)}) goes to Loan 2</small>
        </div>
      </div>
      <div>
        <h4>Loan 2 — Direct Unsubsidized</h4>
        ${_savField('sl_bal2',  'Current Balance ($)',  10)}
        ${_savField('sl_rate2', 'Annual Interest Rate (%)', 0.01)}
        <div class="metrics" style="flex-direction:column;gap:8px;margin-top:8px">
          ${_metric('Loan 1 — Total Interest', fmt(totI1))}
          ${_metric('Loan 1 — Payoff',         loan1Done ? loan1Done.date : 'Month ' + (sched.findIndex(r=>r.b1===0)+1||'—'))}
          ${_metric('Loan 2 — Total Interest', fmt(totI2))}
          ${_metric('Loan 2 — Payoff',         loan2Done ? loan2Done.date : '—')}
        </div>
      </div>
    </div>

    <div class="chart-wrapper tall">
      <canvas id="chart-sl-bal"></canvas>
    </div>

    <h4>Payoff Schedule (first 60 months)</h4>
    <div class="data-table-wrapper">
      <table>
        <thead><tr>
          <th>#</th><th>Date</th>
          <th>Loan 1 Interest</th><th>Loan 1 Payment</th><th>Loan 1 Balance</th>
          <th>Loan 2 Interest</th><th>Loan 2 Payment</th><th>Loan 2 Balance</th>
        </tr></thead>
        <tbody>
          ${sched.slice(0,60).map(r=>`
            <tr>
              <td>${r.month}</td><td>${r.date}</td>
              <td class="amt-red">${fmt(r.i1)}</td>
              <td>${fmt(r.p1)}</td>
              <td>${fmt(r.b1)}</td>
              <td class="amt-red">${fmt(r.i2)}</td>
              <td>${fmt(r.p2)}</td>
              <td>${fmt(r.b2)}</td>
            </tr>`).join('')}
        </tbody>
      </table>
    </div>`;

  _bindSavNum(el, 'sl_bal1',  v => { S.sl_bal1  = v; scheduleRerender('savings'); });
  _bindSavNum(el, 'sl_rate1', v => { S.sl_rate1 = v; scheduleRerender('savings'); });
  _bindSavNum(el, 'sl_bal2',  v => { S.sl_bal2  = v; scheduleRerender('savings'); });
  _bindSavNum(el, 'sl_rate2', v => { S.sl_rate2 = v; scheduleRerender('savings'); });

  const pay1Slider = document.getElementById('sl-pay1');
  if (pay1Slider) {
    pay1Slider.addEventListener('input', () => {
      S.sl_pay1 = parseFloat(pay1Slider.value) || 0;
      scheduleRerender('savings');
    });
  }

  setTimeout(() => {
    createLineChart('chart-sl-bal', [
      { label:'Loan 1 Balance', data:sched.map(r=>r.b1), borderColor:'#4f8ef7', backgroundColor:'rgba(79,142,247,0.1)', fill:true, pointRadius:1.5, borderWidth:2 },
      { label:'Loan 2 Balance', data:sched.map(r=>r.b2), borderColor:'#f39c12', backgroundColor:'rgba(243,156,18,0.1)',  fill:true, pointRadius:1.5, borderWidth:2 },
    ], sched.map(r=>r.date), {
      plugins: { title:{ display:true, text:'Student Loan Balances Over Time', color:'#ccc' } },
    });
  }, 0);
}

/* ── Shared helpers ──────────────────────────────────────────────────────── */
function _savField(key, label, step = 1) {
  const val = typeof S[key] === 'number' ? S[key] : 0;
  return `
  <div class="input-group" style="margin-bottom:14px">
    <label for="sav-${key}">${label}</label>
    <input type="number" id="sav-${key}" value="${val.toFixed(step < 1 ? 2 : 0)}" step="${step}" min="0">
  </div>`;
}

function _metric(label, value) {
  return `
  <div class="metric">
    <div class="metric-label">${label}</div>
    <div class="metric-value">${value}</div>
  </div>`;
}

function _bindSavNum(_container, key, callback) {
  const el = document.getElementById('sav-' + key);
  if (!el) return;
  el.addEventListener('change', () => callback(parseFloat(el.value) || 0));
}

function _bindSlider(sliderId, valId, callback) {
  const slider = document.getElementById(sliderId);
  const valEl  = document.getElementById(valId);
  if (!slider) return;
  slider.addEventListener('input', () => {
    const v = parseInt(slider.value);
    if (valEl) valEl.textContent = v;
    callback(v);
    scheduleRerender('savings');
  });
}
