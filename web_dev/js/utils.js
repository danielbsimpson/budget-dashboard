/* utils.js – Shared helpers: formatting, dates, ledger building */

/* ── Formatting ──────────────────────────────────────────────────────────── */
function fmt(val) {
  if (typeof val !== 'number' || isNaN(val)) return '$0.00';
  return '$' + Math.abs(val).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtSigned(val) {
  const sign = val >= 0 ? '+' : '-';
  return sign + fmt(val);
}

/* ── Date helpers ────────────────────────────────────────────────────────── */
function daysInMonth(year, month) {
  // month is 0-indexed (JS convention)
  return new Date(year, month + 1, 0).getDate();
}

/**
 * All days in (year, month) that fall on `weekday`.
 * weekday: 0=Mon … 6=Sun  (Python convention used throughout app)
 */
function getDaysOfWeek(year, month, weekday) {
  // Convert Python weekday (0=Mon) → JS getDay() (0=Sun)
  const jsDay = (weekday + 1) % 7;
  const total = daysInMonth(year, month);
  const result = [];
  for (let d = 1; d <= total; d++) {
    if (new Date(year, month, d).getDay() === jsDay) result.push(d);
  }
  return result;
}

function getPaydays(year, month) {
  const freq  = S.pay_frequency;
  const total = daysInMonth(year, month);

  if (freq === 'Weekly') {
    return getDaysOfWeek(year, month, S.pay_weekday_idx);
  }

  if (freq === 'Bi-Weekly') {
    const anchor = new Date(S.pay_biweekly_anchor + 'T00:00:00');
    const monthStart = new Date(year, month, 1);
    const monthEnd   = new Date(year, month, total);
    // Walk anchor backward to before monthStart, then forward by 2-week steps
    let d = new Date(anchor);
    while (d > monthStart) d.setDate(d.getDate() - 14);
    while (d < monthStart) d.setDate(d.getDate() + 14);
    const days = [];
    while (d <= monthEnd) {
      if (d.getMonth() === month) days.push(d.getDate());
      d = new Date(d);
      d.setDate(d.getDate() + 14);
    }
    return days;
  }

  // Monthly
  return [Math.min(S.pay_monthly_day, total)];
}

function clampDay(year, month, day) {
  return Math.min(Math.max(1, day), daysInMonth(year, month));
}

/* ── Expense builders ────────────────────────────────────────────────────── */
function buildExpensesCurrent(year, month) {
  const total    = daysInMonth(year, month);
  const expenses = [];

  // Paychecks
  for (const d of getPaydays(year, month)) {
    expenses.push({ day: d, description: 'Payday 💰', amount: -S.paycheck_amount, category: 'Income' });
  }

  // Weekly recurring
  for (const wk of S.weekly_expenses) {
    if (!wk.name || wk.amount <= 0) continue;
    for (const d of getDaysOfWeek(year, month, wk.weekday)) {
      expenses.push({ day: d, description: wk.name, amount: wk.amount, category: 'Weekly' });
    }
  }

  // Recurring bills
  for (const key of Object.keys(REC_DEFAULTS)) {
    const entry = S[key];
    if (!entry || entry.amount <= 0) continue;
    expenses.push({
      day:         clampDay(year, month, entry.day),
      description: REC_DEFAULTS[key].label,
      amount:      entry.amount,
      category:    key.startsWith('rec_rent') || key === 'rec_parking' || key === 'rec_gas' ||
                   key === 'rec_elec' || key === 'rec_water' || key === 'rec_sewer'
                   ? 'Housing' : 'Bills',
    });
  }

  // Additional income
  for (const row of S.add_income_rows) {
    if (!row.description || row.amount <= 0) continue;
    expenses.push({
      day:         clampDay(year, month, row.day || 1),
      description: row.description,
      amount:      -row.amount,   // negative = income
      category:    'Income',
    });
  }

  // One-time expenses
  for (const row of S.oe_expense_rows) {
    if (!row.name || row.amount <= 0) continue;
    expenses.push({
      day:         clampDay(year, month, row.day || 1),
      description: row.name,
      amount:      row.amount,
      category:    'One-off',
    });
  }

  // Credit card payments
  for (const card of S.cc_cards) {
    const amt = parseFloat(card.statement_balance) || 0;
    if (amt <= 0) continue;
    expenses.push({
      day:         clampDay(year, month, card.pay_day),
      description: `${card.name} Payment`,
      amount:      amt,
      category:    'Credit Card',
    });
  }

  return expenses;
}

function buildExpensesNext(year, month, recAmts, recDays) {
  const total    = daysInMonth(year, month);
  const expenses = [];

  // Paychecks
  for (const d of getPaydays(year, month)) {
    expenses.push({ day: d, description: 'Payday 💰', amount: -S.paycheck_amount, category: 'Income' });
  }

  // Weekly recurring
  for (const wk of S.weekly_expenses) {
    if (!wk.name || wk.amount <= 0) continue;
    for (const d of getDaysOfWeek(year, month, wk.weekday)) {
      expenses.push({ day: d, description: wk.name, amount: wk.amount, category: 'Weekly' });
    }
  }

  // Recurring bills using provided amounts/days
  for (const key of Object.keys(REC_DEFAULTS)) {
    const amt = recAmts[key] || 0;
    const day = recDays[key] || 1;
    if (amt <= 0) continue;
    expenses.push({
      day:         clampDay(year, month, day),
      description: REC_DEFAULTS[key].label,
      amount:      amt,
      category:    ['rec_rent','rec_parking','rec_gas','rec_elec','rec_water','rec_sewer'].includes(key)
                   ? 'Housing' : 'Bills',
    });
  }

  // Credit card carry-over (current − statement, if positive)
  for (const card of S.cc_cards) {
    const stmt  = parseFloat(card.statement_balance) || 0;
    const curr  = parseFloat(card.current_balance) || 0;
    const carry = curr > stmt ? curr - stmt : 0;
    if (carry > 0) {
      expenses.push({
        day:         clampDay(year, month, card.pay_day),
        description: `${card.name} carry-over`,
        amount:      carry,
        category:    'Credit Card',
      });
    }
  }

  // Next-month one-offs
  for (const row of S.nm_oe_rows) {
    if (!row.description || row.amount <= 0) continue;
    expenses.push({
      day:         clampDay(year, month, row.day || 1),
      description: row.description,
      amount:      row.amount,
      category:    'One-off',
    });
  }

  return expenses;
}

/* ── Ledger builder ──────────────────────────────────────────────────────── */
/**
 * Returns an array of row objects, one per calendar day.
 * Each row: { day, date, description, amount, runningBalance, hasActivity }
 */
function buildLedger(year, month, expenses, openingBalance) {
  const total = daysInMonth(year, month);

  // Group expenses by day
  const byDay = {};
  for (const e of expenses) {
    (byDay[e.day] = byDay[e.day] || []).push(e);
  }

  const rows = [];
  let running = openingBalance;

  for (let d = 1; d <= total; d++) {
    const dayItems = byDay[d] || [];
    const dayDate  = new Date(year, month, d);

    if (dayItems.length > 0) {
      const income  = dayItems.filter(e => e.amount < 0);
      const outflow = dayItems.filter(e => e.amount >= 0);
      const dayNet  = dayItems.reduce((s, e) => s + e.amount, 0);
      running -= dayNet;  // positive dayNet = net outflow

      const parts = [];
      if (income.length) {
        const names  = income.map(e => e.description).join(', ');
        const total  = income.reduce((s, e) => s + Math.abs(e.amount), 0);
        parts.push(`⬆ ${names} (+${fmt(total)})`);
      }
      if (outflow.length) {
        const names  = outflow.map(e => e.description).join(', ');
        const total  = outflow.reduce((s, e) => s + e.amount, 0);
        parts.push(`⬇ ${names} (-${fmt(total)})`);
      }

      rows.push({
        day: d, date: dayDate,
        description:    parts.join('  |  '),
        amount:         dayNet,
        runningBalance: running,
        hasActivity:    true,
      });
    } else {
      rows.push({
        day: d, date: dayDate,
        description:    '—',
        amount:         0,
        runningBalance: running,
        hasActivity:    false,
      });
    }
  }
  return rows;
}

/**
 * Attaches `actualBalance` to each ledger row.
 * Before today: null  |  at today: currentBalance  |  after: forward projection.
 * Returns projected EOM balance.
 */
function addActualColumn(rows, currentBalance, today) {
  const ty = today.getFullYear(), tm = today.getMonth(), td = today.getDate();
  let running = currentBalance;

  for (const row of rows) {
    const d = row.date;
    const isBefore = d < new Date(ty, tm, td);
    const isToday  = d.getFullYear() === ty && d.getMonth() === tm && d.getDate() === td;

    if (isBefore) {
      row.actualBalance = null;
    } else if (isToday) {
      row.actualBalance = currentBalance;
      running = currentBalance;
    } else {
      running -= row.amount;
      row.actualBalance = running;
    }
  }

  let projEOM = currentBalance;
  for (let i = rows.length - 1; i >= 0; i--) {
    if (rows[i].actualBalance !== null && rows[i].actualBalance !== undefined) {
      projEOM = rows[i].actualBalance;
      break;
    }
  }
  return projEOM;
}

/* ── Simple car amortization ─────────────────────────────────────────────── */
function buildCarAmortization() {
  const balance   = S.car_bal;
  const rate      = S.car_rate / 100 / 12;
  const payment   = S.car_pay;
  const extra     = S.car_extra;
  const start     = new Date(S.car_start + 'T00:00:00');

  let bal = balance;
  const rows = [];
  let cur = new Date(start);
  let monthNum = 0;

  while (bal > 0.01 && monthNum < 600) {
    monthNum++;
    const interest  = parseFloat((bal * rate).toFixed(2));
    let   pmt       = payment + (cur.getMonth() === 3 && monthNum > 1 ? extra : 0);
    pmt = Math.min(pmt, bal + interest);
    const principal = parseFloat((pmt - interest).toFixed(2));
    bal = parseFloat(Math.max(bal - principal, 0).toFixed(2));

    rows.push({
      month: monthNum,
      date:  cur.toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
      payment: pmt,
      interest,
      principal,
      balance: bal,
    });

    // Advance one month
    const next = new Date(cur.getFullYear(), cur.getMonth() + 1, 1);
    cur = next;
  }
  return rows;
}

/* ── 401k projection ─────────────────────────────────────────────────────── */
function build401kProjection() {
  const BASE_LIMIT    = 24500;
  const CATCHUP_50    = 8000;
  const CATCHUP_60_63 = 11250;
  const TOTAL_LIMIT   = 72000;

  function electiveLimit(age) {
    if (age >= 60 && age <= 63) return BASE_LIMIT + CATCHUP_60_63;
    if (age >= 50)              return BASE_LIMIT + CATCHUP_50;
    return BASE_LIMIT;
  }

  const rows = [];
  let balance   = S.k401_cur;
  let curSalary = S.k401_sal;
  const years = S.k401_retire - S.k401_age;

  for (let y = 1; y <= years; y++) {
    const age    = S.k401_age + y;
    const cap    = electiveLimit(age);
    const rawEmp = curSalary * S.k401_pct / 100;
    let   emp    = Math.min(rawEmp, cap);
    let   er     = curSalary * S.k401_emp / 100;
    let   bonus  = S.k401_bonus;
    const total  = emp + er + bonus;
    const scale  = total > TOTAL_LIMIT ? TOTAL_LIMIT / total : 1;
    emp   = parseFloat((emp   * scale).toFixed(2));
    er    = parseFloat((er    * scale).toFixed(2));
    bonus = parseFloat((bonus * scale).toFixed(2));
    balance = parseFloat(((balance + emp + er + bonus) * (1 + S.k401_growth / 100)).toFixed(2));
    rows.push({ year: y, age, salary: curSalary, emp, er, bonus, cap, balance });
    curSalary = y === 1 ? curSalary : parseFloat((curSalary * 1.02).toFixed(2));
  }
  return rows;
}

/* ── Student loan payoff ─────────────────────────────────────────────────── */
function buildStudentLoanSchedule() {
  const pay1    = S.sl_pay1;
  const pay2    = Math.max((S.rec_student.amount || 423) - pay1, 0);
  let   b1      = S.sl_bal1, b2 = S.sl_bal2;
  const r1      = S.sl_rate1 / 100 / 12;
  const r2      = S.sl_rate2 / 100 / 12;
  const rows    = [];
  let month     = 0;
  const today   = new Date();

  while ((b1 > 0.01 || b2 > 0.01) && month < 480) {
    month++;
    const d = new Date(today.getFullYear(), today.getMonth() + month, 1);
    const i1 = parseFloat((b1 * r1).toFixed(2));
    const i2 = parseFloat((b2 * r2).toFixed(2));
    let p1 = Math.min(Math.max(pay1 - i1, 0), b1);
    let p2 = Math.min(Math.max(pay2 - i2, 0), b2);
    if (b1 <= 0.01) { p2 = Math.min(pay1 + pay2 - i2, b2); }
    b1 = parseFloat(Math.max(b1 - p1, 0).toFixed(2));
    b2 = parseFloat(Math.max(b2 - p2, 0).toFixed(2));
    rows.push({
      month, date: d.toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
      i1, p1, b1: b1 > 0.01 ? b1 : 0,
      i2, p2, b2: b2 > 0.01 ? b2 : 0,
    });
  }
  return rows;
}
