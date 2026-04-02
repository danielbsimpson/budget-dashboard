# Supabase Setup for Budget Dashboard

## 1. Create a Supabase project

1. Go to https://supabase.com and sign in.
2. Click **New project**, choose a name (e.g. `budget-sheet`), set a password, pick a region.
3. Wait for the project to provision (~1 min).

---

## 2. Create the `budget_snapshots` table

Open the **SQL Editor** in the Supabase dashboard and run the following:

```sql
-- budget_snapshots: one row per save, newest row is always the active config.
create table if not exists public.budget_snapshots (
    id                    bigserial primary key,
    saved_at              text        not null,          -- ISO-8601 e.g. "2026-04-02T14:30:00"

    -- Income
    paycheck_amount       numeric     not null default 0,
    pay_frequency         text        not null default 'Weekly',
    pay_weekday_idx       integer     not null default 4, -- 0=Mon … 6=Sun
    pay_monthly_day       integer     not null default 1,

    -- Checking balances
    opening_balance       numeric     not null default 0, -- balance on day 1 of month
    current_balance       numeric     not null default 0, -- balance as of last save

    -- Recurring expenses (amount + due-day pairs)
    rec_rent_amount       numeric     not null default 0,
    rec_rent_day          integer     not null default 1,
    rec_parking_amount    numeric     not null default 0,
    rec_parking_day       integer     not null default 1,
    rec_gas_amount        numeric     not null default 0,
    rec_gas_day           integer     not null default 1,
    rec_elec_amount       numeric     not null default 0,
    rec_elec_day          integer     not null default 1,
    rec_water_amount      numeric     not null default 0,
    rec_water_day         integer     not null default 1,
    rec_sewer_amount      numeric     not null default 0,
    rec_sewer_day         integer     not null default 1,
    rec_student_amount    numeric     not null default 0,
    rec_student_day       integer     not null default 1,
    rec_internet_amount   numeric     not null default 0,
    rec_internet_day      integer     not null default 1,
    rec_phone_amount      numeric     not null default 0,
    rec_phone_day         integer     not null default 1,
    rec_insurance_amount  numeric     not null default 0,
    rec_insurance_day     integer     not null default 1,
    rec_subs_amount       numeric     not null default 0,
    rec_subs_day          integer     not null default 1,

    -- JSON blobs
    ai_rows               text        not null default '[]', -- additional income
    oe_expense_rows       text        not null default '[]', -- one-time expenses
    cc_cards              text        not null default '[]'  -- credit cards
);

-- Optional: keep only the last 500 snapshots to avoid unbounded growth
-- (run this as a scheduled function or just manually prune)
-- delete from public.budget_snapshots
-- where id not in (
--     select id from public.budget_snapshots order by saved_at desc limit 500
-- );
```

---

## 3. Set Row Level Security (RLS)

Since this is a personal single-user app, the simplest approach is to use the
**service role key** (keeps the table private) or disable RLS entirely for this
table. Run one of the following:

### Option A — disable RLS (simplest for a private app)
```sql
alter table public.budget_snapshots disable row level security;
```

### Option B — use RLS with anon key allowed full access
```sql
alter table public.budget_snapshots enable row level security;

create policy "allow all" on public.budget_snapshots
    for all using (true) with check (true);
```

---

## 4. Get your credentials

In the Supabase dashboard go to **Project Settings → API**:

| Value | Where to find it |
|---|---|
| `SUPABASE_URL` | "Project URL" field |
| `SUPABASE_KEY` | "anon public" key (Option B above) **or** "service_role" key (Option A) |

---

## 5. Configure secrets

### Local development
Edit `.streamlit/secrets.toml` (already created in the project):

```toml
SUPABASE_URL = "https://xyzabc123.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

> ⚠️ **Never commit real credentials to git.**  
> Add `.streamlit/secrets.toml` to `.gitignore`.

### Streamlit Community Cloud
1. Open your app in the Streamlit Cloud dashboard.
2. Go to **Settings → Secrets**.
3. Paste:
```toml
SUPABASE_URL = "https://xyzabc123.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## 6. Seed an initial row (optional)

If you want the deployed app to start with your current defaults rather than
blank inputs, run this after deploying once locally (which writes to the CSV),
then manually insert the same values via the Supabase **Table Editor** or SQL:

```sql
insert into public.budget_snapshots (
    saved_at, paycheck_amount, pay_frequency, pay_weekday_idx, pay_monthly_day,
    opening_balance, current_balance,
    rec_rent_amount, rec_rent_day,
    rec_parking_amount, rec_parking_day,
    rec_gas_amount, rec_gas_day,
    rec_elec_amount, rec_elec_day,
    rec_water_amount, rec_water_day,
    rec_sewer_amount, rec_sewer_day,
    rec_student_amount, rec_student_day,
    rec_internet_amount, rec_internet_day,
    rec_phone_amount, rec_phone_day,
    rec_insurance_amount, rec_insurance_day,
    rec_subs_amount, rec_subs_day,
    ai_rows, oe_expense_rows, cc_cards
) values (
    now()::text, 1490.00, 'Weekly', 4, 1,
    2883.84, 2883.84,
    2898.00, 2,
    75.00, 2,
    85.00, 2,
    100.00, 2,
    55.00, 2,
    120.00, 2,
    423.00, 10,
    69.99, 26,
    90.04, 29,
    150.00, 3,
    47.00, 24,
    '[]', '[]',
    '[{"name":"Discover","statement_balance":1213.97,"current_balance":0.0,"pay_day":8},{"name":"MasterCard","statement_balance":1288.45,"current_balance":0.0,"pay_day":17}]'
);
```

---

## 8. Future Savings table (`future_snapshots`)

Run this in the SQL Editor to create the second table:

```sql
create table if not exists public.future_snapshots (
    id               bigserial primary key,
    saved_at         text    not null,

    -- Savings Overview
    ally             numeric not null default 0,
    burke            numeric not null default 0,
    rh               numeric not null default 0,
    schwab           numeric not null default 0,
    merill           numeric not null default 0,
    sav_checking     numeric not null default 0,
    sav_goal         numeric not null default 0,
    monthly_save     numeric not null default 0,
    sav_months       integer not null default 24,

    -- Mortgage Down Payment
    hp               numeric not null default 0,
    dp_pct           integer not null default 10,
    dp_saved         numeric not null default 0,
    dp_monthly       numeric not null default 0,

    -- Car Loan
    car_bal          numeric not null default 0,
    car_rate         numeric not null default 0,
    car_pay          numeric not null default 0,
    car_extra        numeric not null default 0,
    car_start        text    not null default '2025-01-01',

    -- 401k
    k401_cur         numeric not null default 0,
    k401_sal         numeric not null default 0,
    k401_pct         integer not null default 10,
    k401_emp         integer not null default 4,
    k401_growth      integer not null default 6,
    k401_bonus       numeric not null default 0,
    k401_age         integer not null default 30,
    k401_retire      integer not null default 65
);

-- Apply same RLS choice as budget_snapshots
alter table public.future_snapshots disable row level security;
-- or: enable row level security + create policy (see Step 3 above)
```


| Environment | `SUPABASE_URL` in secrets | Backend used |
|---|---|---|
| Local dev (no secrets.toml key set) | placeholder / missing | 📄 `current_data.csv` |
| Local dev (real key set) | real URL | ☁️ Supabase |
| Streamlit Community Cloud | real URL (set in Secrets UI) | ☁️ Supabase |

The active backend is shown at the bottom of the sidebar below the **💾 Save All Changes** button.
