/* sidebar.js – Sidebar rendering and event binding */

function renderSidebar() {
  const body = document.getElementById('sidebar-body');
  body.innerHTML = _sbIncome() + _sbRecurring() + _sbCreditCards() + _sbAdditionalIncome() + _sbOneTimeExpenses();
  _bindSidebarEvents();
}

/* ── Income ─────────────────────────────────────────────────────────────── */
function _sbIncome() {
  const freq = S.pay_frequency;
  const freqs = ['Weekly','Bi-Weekly','Monthly'];

  let dynFields = '';
  if (freq === 'Weekly') {
    dynFields = _sbField('Pay day of week', `
      <select id="sb-pay-weekday">
        ${WEEKDAY_NAMES.map((n, i) => `<option value="${i}" ${i === S.pay_weekday_idx ? 'selected' : ''}>${n}</option>`).join('')}
      </select>
      <div class="caption" id="sb-payday-caption">📅 Paydays: every <strong>${WEEKDAY_NAMES[S.pay_weekday_idx]}</strong></div>
    `);
  } else if (freq === 'Bi-Weekly') {
    dynFields = _sbField('Pay day of week', `
      <select id="sb-pay-weekday">
        ${WEEKDAY_NAMES.map((n, i) => `<option value="${i}" ${i === S.pay_weekday_idx ? 'selected' : ''}>${n}</option>`).join('')}
      </select>
    `) + _sbField('Reference payday (anchor)', `
      <input type="date" id="sb-biweekly-anchor" value="${S.pay_biweekly_anchor}">
      <div class="caption">Used to determine which weeks you're paid.</div>
    `);
  } else {
    dynFields = _sbField('Payday (day of month)', `
      <input type="number" id="sb-monthly-day" value="${S.pay_monthly_day}" min="1" max="31" step="1">
    `);
  }

  return `
  <div class="sb-section">
    <h3>💵 Income</h3>
    ${_sbField('Paycheck Amount ($)', `<input type="number" id="sb-paycheck" value="${S.paycheck_amount.toFixed(2)}" min="0" step="10">`)}
    <div class="field">
      <label>Pay Frequency</label>
      <div class="radio-group">
        ${freqs.map(f => `
          <label>
            <input type="radio" name="pay-freq" value="${f}" ${f === freq ? 'checked' : ''}> ${f}
          </label>`).join('')}
      </div>
    </div>
    <div id="sb-pay-dyn">${dynFields}</div>
    <div class="caption">💵 Amount: <strong>${fmt(S.paycheck_amount)}</strong> per paycheck</div>
  </div>`;
}

/* ── Recurring expenses ──────────────────────────────────────────────────── */
function _sbRecurring() {
  const housingKeys  = ['rec_rent','rec_parking','rec_gas','rec_elec','rec_water','rec_sewer'];
  const billKeys     = ['rec_student','rec_internet','rec_phone','rec_insurance','rec_subs'];

  const housingRows  = housingKeys.map(k => _sbRecRow(k)).join('');
  const billRows     = billKeys.map(k => _sbRecRow(k)).join('');
  const weeklyRows   = _sbWeeklyExpenses();

  return `
  <div class="sb-section">
    <h3>📉 Recurring Expenses</h3>
    ${_sbExpander('sb-exp-housing', '🏠 Housing &amp; Utilities', housingRows)}
    ${_sbExpander('sb-exp-bills',   '📡 Bills &amp; Subscriptions', billRows)}
    ${_sbExpander('sb-exp-weekly',  '🔄 Weekly Expenses', weeklyRows, 'sb-weekly-add-row')}
  </div>`;
}

function _sbRecRow(key) {
  const entry = S[key];
  const label = REC_DEFAULTS[key].label;
  return `
  <div class="col2" style="margin-bottom:8px">
    <div class="field">
      <label>${label} ($)</label>
      <input type="number" class="rec-amt" data-key="${key}" value="${entry.amount.toFixed(2)}" min="0" step="0.01">
    </div>
    <div class="field" style="width:72px">
      <label>Day</label>
      <input type="number" class="rec-day" data-key="${key}" value="${entry.day}" min="1" max="31" step="1">
    </div>
  </div>`;
}

function _sbWeeklyExpenses() {
  let rows = S.weekly_expenses.map((wk, i) => `
    <div class="row-item" data-wk-idx="${i}">
      <div class="row-item-header">
        <span>Expense #${i + 1}</span>
        <button class="btn btn-sm btn-danger wk-del" data-idx="${i}">🗑</button>
      </div>
      <div class="field"><label>Name</label>
        <input type="text" class="wk-name" data-idx="${i}" value="${_esc(wk.name)}" placeholder="e.g. Groceries">
      </div>
      <div class="col2">
        <div class="field"><label>Amount ($)</label>
          <input type="number" class="wk-amt" data-idx="${i}" value="${wk.amount.toFixed(2)}" min="0" step="0.01">
        </div>
        <div class="field" style="min-width:90px"><label>Day of week</label>
          <select class="wk-day" data-idx="${i}">
            ${WEEKDAY_NAMES.map((n, d) => `<option value="${d}" ${d === wk.weekday ? 'selected' : ''}>${n.slice(0,3)}</option>`).join('')}
          </select>
        </div>
      </div>
    </div>`).join('');

  return rows + `<button class="btn btn-sm add-row-btn" id="sb-wk-add">➕ Add Weekly Expense</button>`;
}

/* ── Credit cards ────────────────────────────────────────────────────────── */
function _sbCreditCards() {
  const cards = S.cc_cards.map((card, i) => `
    <div class="row-item">
      <div class="row-item-header"><span>💳 ${_esc(card.name)}</span></div>
      <div class="field"><label>Card Name</label>
        <input type="text" class="cc-name" data-idx="${i}" value="${_esc(card.name)}">
      </div>
      <div class="col2">
        <div class="field"><label>Statement Balance ($)</label>
          <input type="number" class="cc-stmt" data-idx="${i}" value="${card.statement_balance.toFixed(2)}" min="0" step="0.01">
        </div>
        <div class="field" style="width:80px"><label>Pay Day</label>
          <input type="number" class="cc-pday" data-idx="${i}" value="${card.pay_day}" min="1" max="31" step="1">
        </div>
      </div>
      <div class="field"><label>Current Running Balance ($)</label>
        <input type="number" class="cc-curr" data-idx="${i}" value="${card.current_balance.toFixed(2)}" min="0" step="0.01">
        <small>Used to calculate carry-over to next month.</small>
      </div>
    </div>`).join('');

  const ccContent = `<div id="sb-cards">${cards}</div>
    <button class="btn btn-sm add-row-btn" id="sb-cc-add">➕ Add Card</button>`;

  return `
  <div class="sb-section">
    <h3>💳 Credit Cards</h3>
    ${_sbExpander('sb-exp-cards', '💳 Cards', ccContent)}
  </div>`;
}

/* ── Additional income ───────────────────────────────────────────────────── */
function _sbAdditionalIncome() {
  const rows = S.add_income_rows.map((row, i) => `
    <div class="row-item">
      <div class="row-item-header">
        <span>Income #${i + 1}</span>
        <button class="btn btn-sm btn-danger ai-del" data-idx="${i}">🗑</button>
      </div>
      <div class="field"><label>Description</label>
        <input type="text" class="ai-desc" data-idx="${i}" value="${_esc(row.description || '')}" placeholder="e.g. Bonus">
      </div>
      <div class="col2">
        <div class="field"><label>Amount ($)</label>
          <input type="number" class="ai-amt" data-idx="${i}" value="${(row.amount || 0).toFixed(2)}" min="0" step="1">
        </div>
        <div class="field" style="width:72px"><label>Day</label>
          <input type="number" class="ai-day" data-idx="${i}" value="${row.day || 1}" min="1" max="31" step="1">
        </div>
      </div>
    </div>`).join('');

  const totalAI = S.add_income_rows.reduce((s, r) => s + (r.amount || 0), 0);

  return `
  <div class="sb-section">
    <h3>💸 Additional Income</h3>
    <p class="caption">One-time income this month (bonus, side work, etc.)</p>
    <div id="sb-ai-rows">${rows}</div>
    <button class="btn btn-sm add-row-btn" id="sb-ai-add">➕ Add Income</button>
    ${totalAI > 0 ? `<div class="caption" style="margin-top:6px">Total additional: <strong>${fmt(totalAI)}</strong></div>` : ''}
  </div>`;
}

/* ── One-time expenses ───────────────────────────────────────────────────── */
function _sbOneTimeExpenses() {
  const rows = S.oe_expense_rows.map((row, i) => `
    <div class="row-item">
      <div class="row-item-header">
        <span>Expense #${i + 1}</span>
        <button class="btn btn-sm btn-danger oe-del" data-idx="${i}">🗑</button>
      </div>
      <div class="field"><label>Name</label>
        <input type="text" class="oe-name" data-idx="${i}" value="${_esc(row.name || '')}" placeholder="e.g. Car Repair">
      </div>
      <div class="col2">
        <div class="field"><label>Amount ($)</label>
          <input type="number" class="oe-amt" data-idx="${i}" value="${(row.amount || 0).toFixed(2)}" min="0" step="1">
        </div>
        <div class="field" style="width:72px"><label>Day</label>
          <input type="number" class="oe-day" data-idx="${i}" value="${row.day || 1}" min="1" max="31" step="1">
        </div>
      </div>
    </div>`).join('');

  return `
  <div class="sb-section">
    <h3>🧾 One-time Expenses</h3>
    <p class="caption">Non-recurring expenses this month</p>
    <div id="sb-oe-rows">${rows}</div>
    <button class="btn btn-sm add-row-btn" id="sb-oe-add">➕ Add Expense</button>
  </div>`;
}

/* ── Helpers ─────────────────────────────────────────────────────────────── */
function _sbField(label, inputHtml) {
  return `<div class="field"><label>${label}</label>${inputHtml}</div>`;
}

function _sbExpander(id, title, content) {
  return `
  <div class="expander" id="${id}">
    <button class="expander-toggle" onclick="_toggleExpander('${id}')">
      <span>${title}</span><i class="chevron">›</i>
    </button>
    <div class="expander-body">
      ${content}
    </div>
  </div>`;
}

function _toggleExpander(id) {
  const el = document.getElementById(id);
  if (!el) return;
  const btn  = el.querySelector('.expander-toggle');
  const body = el.querySelector('.expander-body');
  btn.classList.toggle('open');
  body.classList.toggle('open');
}

function _esc(str) {
  return String(str).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;');
}

/* ── Event binding ───────────────────────────────────────────────────────── */
function _bindSidebarEvents() {
  const body = document.getElementById('sidebar-body');

  /* paycheck */
  _live('sb-paycheck', v => { S.paycheck_amount = v; scheduleRerender(); });

  /* pay frequency radios */
  body.querySelectorAll('input[name="pay-freq"]').forEach(r => {
    r.addEventListener('change', () => { S.pay_frequency = r.value; renderSidebar(); scheduleRerender(); });
  });

  /* dynamic pay fields */
  const wdSel = document.getElementById('sb-pay-weekday');
  if (wdSel) {
    wdSel.addEventListener('change', () => { S.pay_weekday_idx = parseInt(wdSel.value); scheduleRerender(); });
  }
  const anchor = document.getElementById('sb-biweekly-anchor');
  if (anchor) {
    anchor.addEventListener('change', () => { S.pay_biweekly_anchor = anchor.value; scheduleRerender(); });
  }
  const mDay = document.getElementById('sb-monthly-day');
  if (mDay) {
    mDay.addEventListener('change', () => { S.pay_monthly_day = parseInt(mDay.value) || 1; scheduleRerender(); });
  }

  /* recurring: amount */
  body.querySelectorAll('.rec-amt').forEach(el => {
    el.addEventListener('change', () => {
      const key = el.dataset.key;
      S[key] = { ...S[key], amount: parseFloat(el.value) || 0 };
      scheduleRerender();
    });
  });
  /* recurring: day */
  body.querySelectorAll('.rec-day').forEach(el => {
    el.addEventListener('change', () => {
      const key = el.dataset.key;
      S[key] = { ...S[key], day: parseInt(el.value) || 1 };
      scheduleRerender();
    });
  });

  /* credit cards */
  body.querySelectorAll('.cc-name').forEach(el => el.addEventListener('input', () => {
    S.cc_cards[+el.dataset.idx].name = el.value; scheduleRerender();
  }));
  body.querySelectorAll('.cc-stmt').forEach(el => el.addEventListener('change', () => {
    S.cc_cards[+el.dataset.idx].statement_balance = parseFloat(el.value) || 0; scheduleRerender();
  }));
  body.querySelectorAll('.cc-curr').forEach(el => el.addEventListener('change', () => {
    S.cc_cards[+el.dataset.idx].current_balance = parseFloat(el.value) || 0; scheduleRerender();
  }));
  body.querySelectorAll('.cc-pday').forEach(el => el.addEventListener('change', () => {
    S.cc_cards[+el.dataset.idx].pay_day = parseInt(el.value) || 1; scheduleRerender();
  }));
  const addCC = document.getElementById('sb-cc-add');
  if (addCC) addCC.addEventListener('click', () => {
    S.cc_cards.push({ name: 'New Card', statement_balance: 0, current_balance: 0, pay_day: 15 });
    renderSidebar(); scheduleRerender();
  });

  /* weekly expenses */
  body.querySelectorAll('.wk-name').forEach(el => el.addEventListener('input', () => {
    S.weekly_expenses[+el.dataset.idx].name = el.value; scheduleRerender();
  }));
  body.querySelectorAll('.wk-amt').forEach(el => el.addEventListener('change', () => {
    S.weekly_expenses[+el.dataset.idx].amount = parseFloat(el.value) || 0; scheduleRerender();
  }));
  body.querySelectorAll('.wk-day').forEach(el => el.addEventListener('change', () => {
    S.weekly_expenses[+el.dataset.idx].weekday = parseInt(el.value); scheduleRerender();
  }));
  body.querySelectorAll('.wk-del').forEach(el => el.addEventListener('click', () => {
    S.weekly_expenses.splice(+el.dataset.idx, 1); renderSidebar(); scheduleRerender();
  }));
  const addWk = document.getElementById('sb-wk-add');
  if (addWk) addWk.addEventListener('click', () => {
    S.weekly_expenses.push({ name: '', amount: 0, weekday: 0 });
    renderSidebar(); scheduleRerender();
  });

  /* additional income */
  body.querySelectorAll('.ai-desc').forEach(el => el.addEventListener('input', () => {
    S.add_income_rows[+el.dataset.idx].description = el.value; scheduleRerender();
  }));
  body.querySelectorAll('.ai-amt').forEach(el => el.addEventListener('change', () => {
    S.add_income_rows[+el.dataset.idx].amount = parseFloat(el.value) || 0; scheduleRerender();
  }));
  body.querySelectorAll('.ai-day').forEach(el => el.addEventListener('change', () => {
    S.add_income_rows[+el.dataset.idx].day = parseInt(el.value) || 1; scheduleRerender();
  }));
  body.querySelectorAll('.ai-del').forEach(el => el.addEventListener('click', () => {
    S.add_income_rows.splice(+el.dataset.idx, 1); renderSidebar(); scheduleRerender();
  }));
  const addAI = document.getElementById('sb-ai-add');
  if (addAI) addAI.addEventListener('click', () => {
    S.add_income_rows.push({ description: '', amount: 0, day: 1 });
    renderSidebar(); scheduleRerender();
  });

  /* one-time expenses */
  body.querySelectorAll('.oe-name').forEach(el => el.addEventListener('input', () => {
    S.oe_expense_rows[+el.dataset.idx].name = el.value; scheduleRerender();
  }));
  body.querySelectorAll('.oe-amt').forEach(el => el.addEventListener('change', () => {
    S.oe_expense_rows[+el.dataset.idx].amount = parseFloat(el.value) || 0; scheduleRerender();
  }));
  body.querySelectorAll('.oe-day').forEach(el => el.addEventListener('change', () => {
    S.oe_expense_rows[+el.dataset.idx].day = parseInt(el.value) || 1; scheduleRerender();
  }));
  body.querySelectorAll('.oe-del').forEach(el => el.addEventListener('click', () => {
    S.oe_expense_rows.splice(+el.dataset.idx, 1); renderSidebar(); scheduleRerender();
  }));
  const addOE = document.getElementById('sb-oe-add');
  if (addOE) addOE.addEventListener('click', () => {
    S.oe_expense_rows.push({ name: '', amount: 0, day: 1 });
    renderSidebar(); scheduleRerender();
  });
}

/* Generic live number-input binder */
function _live(id, callback) {
  const el = document.getElementById(id);
  if (!el) return;
  el.addEventListener('change', () => callback(parseFloat(el.value) || 0));
}
