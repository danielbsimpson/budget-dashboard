/* state.js – Application state and defaults */

const WEEKDAY_NAMES = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];

const REC_DEFAULTS = {
  rec_rent:      { label: 'Rent',          amount: 1450.00, day: 1  },
  rec_parking:   { label: 'Parking',        amount:   50.00, day: 1  },
  rec_gas:       { label: 'Gas',            amount:   80.00, day: 7  },
  rec_elec:      { label: 'Electricity',    amount:  130.00, day: 7  },
  rec_water:     { label: 'Water',          amount:   45.00, day: 2  },
  rec_sewer:     { label: 'Sewage',         amount:   35.00, day: 2  },
  rec_student:   { label: 'Student Loans',  amount:  385.00, day: 10 },
  rec_internet:  { label: 'Internet',       amount:   65.00, day: 26 },
  rec_phone:     { label: 'Phone',          amount:   75.00, day: 29 },
  rec_insurance: { label: 'Insurance',      amount:  175.00, day: 3  },
  rec_subs:      { label: 'Subscriptions',  amount:   45.00, day: 24 },
};

const DEMO_STATE = {
  /* ── Income ── */
  paycheck_amount:     1700.00,
  pay_frequency:       'Bi-Weekly', // 'Weekly' | 'Bi-Weekly' | 'Monthly'
  pay_weekday_idx:     4,            // 0=Mon … 6=Sun  (Friday)
  pay_biweekly_anchor: '2026-04-10',
  pay_monthly_day:     1,

  /* ── Current month ── */
  cm_opening:     3200.00,
  cm_current_bal: 1650.00,

  /* ── Recurring bills ── */
  rec_rent:      { amount: 1450.00, day: 1  },
  rec_parking:   { amount:   50.00, day: 1  },
  rec_gas:       { amount:   80.00, day: 7  },
  rec_elec:      { amount:  130.00, day: 7  },
  rec_water:     { amount:   45.00, day: 2  },
  rec_sewer:     { amount:   35.00, day: 2  },
  rec_student:   { amount:  385.00, day: 10 },
  rec_internet:  { amount:   65.00, day: 26 },
  rec_phone:     { amount:   75.00, day: 29 },
  rec_insurance: { amount:  175.00, day: 3  },
  rec_subs:      { amount:   45.00, day: 24 },

  /* ── Credit cards ── */
  cc_cards: [
    { name: 'Chase Visa',   statement_balance: 2400.00, current_balance: 0.0, pay_day: 10 },
    { name: 'Capital One',  statement_balance: 1800.00, current_balance: 0.0, pay_day: 22 },
  ],

  /* ── Weekly expenses ── */
  weekly_expenses: [
    { name: 'Groceries',  amount: 100.00, weekday: 5 },
    { name: 'Dining Out', amount:  55.00, weekday: 4 },
  ],

  /* ── Additional income / one-offs ── */
  add_income_rows:  [],
  oe_expense_rows:  [],

  /* ── Next-month one-offs ── */
  nm_oe_rows: [
    { description: 'Entertainment / Fun', amount: 100.0, day: 15 },
  ],
  /* next-month overrides: null = use sidebar value */
  nm_overrides:     {},
  nm_day_overrides: {},

  /* ── Future savings ── */
  ally:          4800.00,
  burke:         1200.00,
  rh:            1500.00,
  schwab:        9500.00,
  merill:       12000.00,
  sav_checking:  3200.00,
  sav_goal:     30000.00,
  monthly_save:   400.00,
  sav_months:      18,

  /* ── Mortgage ── */
  hp:           280000.0,
  dp_pct:            10,
  dp_saved:       8000.0,
  dp_monthly:      400.0,

  /* ── Car loan ── */
  car_bal:      18500.00,
  car_rate:         7.50,
  car_pay:        450.00,
  car_extra:        0.00,
  car_start:   '2023-09-01',

  /* ── 401k ── */
  k401_cur:    14500.00,
  k401_sal:    60000.00,
  k401_pct:         6,
  k401_emp:         3,
  k401_growth:      7,
  k401_bonus:       0.00,
  k401_age:        32,
  k401_retire:     65,

  /* ── Student loans ── */
  sl_bal1:   12500.00,
  sl_rate1:      5.50,
  sl_bal2:   24000.00,
  sl_rate2:      6.54,
  sl_pay1:     400.00,

  /* ── Internal (computed, not persisted) ── */
  _cm_projected_eom: 0.0,
};

/* Live state */
let S = JSON.parse(JSON.stringify(DEMO_STATE));

/* ── Load from demo.json if available ────────────────────────────────────── */
async function loadDemoData() {
  try {
    const resp = await fetch('data/demo.json');
    if (!resp.ok) return;
    const data = await resp.json();
    _mergeState(data);
  } catch (_) { /* silent fallback to built-in defaults */ }
}

function _mergeState(data) {
  const flatKeys = [
    'paycheck_amount','pay_frequency','pay_weekday_idx','pay_biweekly_anchor','pay_monthly_day',
    'cm_opening','cm_current_bal',
    'ally','burke','rh','schwab','merill','sav_checking','sav_goal','monthly_save','sav_months',
    'hp','dp_pct','dp_saved','dp_monthly',
    'car_bal','car_rate','car_pay','car_extra','car_start',
    'k401_cur','k401_sal','k401_pct','k401_emp','k401_growth','k401_bonus','k401_age','k401_retire',
    'sl_bal1','sl_rate1','sl_bal2','sl_rate2','sl_pay1',
  ];
  for (const k of flatKeys) if (k in data) S[k] = data[k];

  for (const key of Object.keys(REC_DEFAULTS)) {
    if (key in data && data[key] && typeof data[key] === 'object') S[key] = { ...data[key] };
  }
  if (Array.isArray(data.cc_cards))        S.cc_cards        = JSON.parse(JSON.stringify(data.cc_cards));
  if (Array.isArray(data.weekly_expenses)) S.weekly_expenses = JSON.parse(JSON.stringify(data.weekly_expenses));
  if (Array.isArray(data.add_income_rows)) S.add_income_rows = JSON.parse(JSON.stringify(data.add_income_rows));
  if (Array.isArray(data.oe_expense_rows)) S.oe_expense_rows = JSON.parse(JSON.stringify(data.oe_expense_rows));
  if (Array.isArray(data.nm_oe_rows))      S.nm_oe_rows      = JSON.parse(JSON.stringify(data.nm_oe_rows));
}
