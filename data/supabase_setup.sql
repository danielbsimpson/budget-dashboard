-- =============================================================================
-- Budget Dashboard — Supabase Setup SQL
-- Generated: 2026-04-02
--
-- Run the entire file in the Supabase SQL Editor (in order):
--   1. Create tables
--   2. Disable Row Level Security (single-user personal app)
--   3. Seed each table with the latest values from your local CSV files
--
-- After running this, add your SUPABASE_URL and SUPABASE_KEY to
-- .streamlit/secrets.toml (local) or the Streamlit Cloud Secrets UI (cloud).
-- =============================================================================


-- =============================================================================
-- SECTION 1 — budget_snapshots
-- Stores sidebar state: income, recurring bills, credit cards, balances.
-- The app always reads the most recently saved row (ordered by saved_at desc).
-- =============================================================================

create table if not exists public.budget_snapshots (
    id                    bigserial    primary key,
    saved_at              text         not null,   -- ISO-8601 e.g. "2026-04-02T14:30:00"

    -- ── Income ────────────────────────────────────────────────────────────────
    paycheck_amount       numeric      not null default 0,
    pay_frequency         text         not null default 'Weekly',  -- 'Weekly' | 'Monthly'
    pay_weekday_idx       integer      not null default 4,         -- 0=Mon … 6=Sun
    pay_monthly_day       integer      not null default 1,

    -- ── Checking balances ─────────────────────────────────────────────────────
    opening_balance       numeric      not null default 0,   -- balance on day 1 of month
    current_balance       numeric      not null default 0,   -- balance as of last save

    -- ── Recurring expenses (amount + due-day pairs) ───────────────────────────
    rec_rent_amount       numeric      not null default 0,
    rec_rent_day          integer      not null default 1,
    rec_parking_amount    numeric      not null default 0,
    rec_parking_day       integer      not null default 1,
    rec_gas_amount        numeric      not null default 0,
    rec_gas_day           integer      not null default 1,
    rec_elec_amount       numeric      not null default 0,
    rec_elec_day          integer      not null default 1,
    rec_water_amount      numeric      not null default 0,
    rec_water_day         integer      not null default 1,
    rec_sewer_amount      numeric      not null default 0,
    rec_sewer_day         integer      not null default 1,
    rec_student_amount    numeric      not null default 0,
    rec_student_day       integer      not null default 1,
    rec_internet_amount   numeric      not null default 0,
    rec_internet_day      integer      not null default 1,
    rec_phone_amount      numeric      not null default 0,
    rec_phone_day         integer      not null default 1,
    rec_insurance_amount  numeric      not null default 0,
    rec_insurance_day     integer      not null default 1,
    rec_subs_amount       numeric      not null default 0,
    rec_subs_day          integer      not null default 1,

    -- ── JSON blobs ────────────────────────────────────────────────────────────
    ai_rows               text         not null default '[]',  -- additional income rows
    oe_expense_rows       text         not null default '[]',  -- one-time expense rows
    cc_cards              text         not null default '[]'   -- credit card list
);

-- Single-user personal app — disable RLS for simplest access.
-- If you prefer to use the anon key with RLS enabled, see SUPABASE_SETUP.md.
alter table public.budget_snapshots disable row level security;


-- =============================================================================
-- SECTION 2 — future_snapshots
-- Stores Future Savings tab state: savings accounts, mortgage, car loan,
-- 401k projections, and student loan payoff planner.
-- =============================================================================

create table if not exists public.future_snapshots (
    id               bigserial    primary key,
    saved_at         text         not null,   -- ISO-8601

    -- ── Savings Overview ──────────────────────────────────────────────────────
    ally             numeric      not null default 0,
    burke            numeric      not null default 0,
    rh               numeric      not null default 0,   -- Robinhood
    schwab           numeric      not null default 0,
    merill           numeric      not null default 0,   -- Merrill (TJX)
    sav_checking     numeric      not null default 0,
    sav_goal         numeric      not null default 0,
    monthly_save     numeric      not null default 0,
    sav_months       integer      not null default 24,

    -- ── Mortgage Down Payment ─────────────────────────────────────────────────
    hp               numeric      not null default 0,   -- home price
    dp_pct           integer      not null default 10,  -- down payment %
    dp_saved         numeric      not null default 0,
    dp_monthly       numeric      not null default 0,

    -- ── Car Loan ──────────────────────────────────────────────────────────────
    car_bal          numeric      not null default 0,
    car_rate         numeric      not null default 0,   -- annual interest rate %
    car_pay          numeric      not null default 0,   -- monthly payment
    car_extra        numeric      not null default 0,   -- extra annual payment (April)
    car_start        text         not null default '2025-01-01',  -- ISO date

    -- ── 401k ──────────────────────────────────────────────────────────────────
    k401_cur         numeric      not null default 0,
    k401_sal         numeric      not null default 0,
    k401_pct         integer      not null default 10,  -- employee contribution %
    k401_emp         integer      not null default 4,   -- employer match %
    k401_growth      integer      not null default 6,   -- assumed annual growth %
    k401_bonus       numeric      not null default 0,   -- annual bonus contribution
    k401_age         integer      not null default 30,
    k401_retire      integer      not null default 65,

    -- ── Student Loans ─────────────────────────────────────────────────────────
    sl_bal1          numeric      not null default 6561.77,   -- Loan 1 (Direct Grad PLUS) balance
    sl_rate1         numeric      not null default 6.83,      -- Loan 1 annual interest rate %
    sl_bal2          numeric      not null default 14031.70,  -- Loan 2 (Direct Unsubsidized) balance
    sl_rate2         numeric      not null default 5.83,      -- Loan 2 annual interest rate %
    sl_pay1          numeric      not null default 226.77     -- monthly payment allocated to Loan 1
                                                             -- (Loan 2 payment = total - sl_pay1)
);

alter table public.future_snapshots disable row level security;


-- =============================================================================
-- SECTION 3 — Seed budget_snapshots
-- Values taken from the latest row of current_data.csv (2026-04-02T12:41:56).
--
-- NOTE: ai_rows and oe_expense_rows below reflect the actual saved values from
-- that snapshot. These are April 2026 one-time items — they will be cleared
-- automatically by the app on the next calendar month rollover.
-- To start with a clean slate instead, replace their values with '[]'.
-- =============================================================================

insert into public.budget_snapshots (
    saved_at,
    paycheck_amount,
    pay_frequency,
    pay_weekday_idx,
    pay_monthly_day,
    opening_balance,
    current_balance,
    rec_rent_amount,       rec_rent_day,
    rec_parking_amount,    rec_parking_day,
    rec_gas_amount,        rec_gas_day,
    rec_elec_amount,       rec_elec_day,
    rec_water_amount,      rec_water_day,
    rec_sewer_amount,      rec_sewer_day,
    rec_student_amount,    rec_student_day,
    rec_internet_amount,   rec_internet_day,
    rec_phone_amount,      rec_phone_day,
    rec_insurance_amount,  rec_insurance_day,
    rec_subs_amount,       rec_subs_day,
    ai_rows,
    oe_expense_rows,
    cc_cards
) values (
    '2026-04-02T12:41:56',
    1490.00,               -- paycheck_amount
    'Weekly',              -- pay_frequency
    4,                     -- pay_weekday_idx  (4 = Friday)
    1,                     -- pay_monthly_day  (unused when Weekly)
    2883.84,               -- opening_balance
    242.58,                -- current_balance
    2898.00,  2,           -- rent
    75.00,    2,           -- parking
    85.00,    7,           -- gas
    100.00,   7,           -- electricity
    55.00,    2,           -- water
    120.00,   2,           -- sewer
    423.00,   10,          -- student loans
    69.99,    26,          -- internet
    90.04,    29,          -- phone
    150.00,   3,           -- insurance
    47.00,    24,          -- subscriptions
    -- Additional income (month-specific — set to '[]' if you want a clean start)
    '[{"description": "Bonus", "amount": 14500.0, "day": 3}, {"description": "Savings", "amount": 700.0, "day": 1}]',
    -- One-time expenses (month-specific — set to '[]' if you want a clean start)
    '[{"name": "Desk", "amount": 1320.0, "day": 5}, {"name": "Chair", "amount": 330.0, "day": 5}, {"name": "Monitor", "amount": 880.0, "day": 5}, {"name": "Handheld", "amount": 880.0, "day": 5}, {"name": "Savings Deposit", "amount": 3000.0, "day": 5}, {"name": "Investment Deposit", "amount": 1500.0, "day": 5}, {"name": "Additional Car Payment", "amount": 1000.0, "day": 5}]',
    -- Credit cards
    '[{"name": "Discover", "statement_balance": 2301.44, "current_balance": 0.0, "pay_day": 8}, {"name": "MasterCard", "statement_balance": 4469.0, "current_balance": 0.0, "pay_day": 17}]'
);


-- =============================================================================
-- SECTION 4 — Seed future_snapshots
-- Values taken from the latest row of future_data.csv (2026-04-02T14:00:00),
-- including all student loan fields.
-- =============================================================================

insert into public.future_snapshots (
    saved_at,
    ally, burke, rh, schwab, merill,
    sav_checking, sav_goal, monthly_save, sav_months,
    hp, dp_pct, dp_saved, dp_monthly,
    car_bal, car_rate, car_pay, car_extra, car_start,
    k401_cur, k401_sal, k401_pct, k401_emp,
    k401_growth, k401_bonus, k401_age, k401_retire,
    sl_bal1, sl_rate1,
    sl_bal2, sl_rate2,
    sl_pay1
) values (
    '2026-04-02T14:00:00',
    1025.00,               -- ally savings
    6000.00,               -- burke savings
    843.00,                -- robinhood
    24500.00,              -- charles schwab
    43000.00,              -- merrill (TJX)
    2883.84,               -- checking
    80000.00,              -- savings goal
    1500.00,               -- monthly savings contribution
    36,                    -- months to project
    800000.00,             -- home price
    10,                    -- down payment %
    30500.00,              -- already saved toward down payment
    1000.00,               -- monthly down payment contribution
    29970.98,              -- car loan balance
    7.89,                  -- car loan annual interest rate %
    600.00,                -- monthly car payment
    1000.00,               -- extra annual car payment (April)
    '2026-04-02',          -- car loan start date
    8627.05,               -- current 401k balance
    143000.00,             -- salary
    15,                    -- employee contribution %
    4,                     -- employer match %
    6,                     -- assumed annual growth %
    3000.00,               -- annual bonus contribution to 401k
    36,                    -- current age
    65,                    -- target retirement age
    6561.77,               -- Loan 1 (Direct Grad PLUS) balance
    6.83,                  -- Loan 1 annual interest rate %
    14031.70,              -- Loan 2 (Direct Unsubsidized) balance
    5.83,                  -- Loan 2 annual interest rate %
    226.77                 -- monthly payment to Loan 1 ($195.33 auto-assigned to Loan 2)
);


-- =============================================================================
-- VERIFICATION — run these selects after inserting to confirm the rows landed.
-- =============================================================================

-- select * from public.budget_snapshots  order by saved_at desc limit 1;
-- select * from public.future_snapshots  order by saved_at desc limit 1;
