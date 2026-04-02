# 💰 Personal Budget Dashboard

A personal finance dashboard built with [Streamlit](https://streamlit.io) that helps you track spending, project account balances, and plan for future savings — all in one place.

---

## ✨ Features

### 📅 Tab 1 — Current Month
- Enter your **opening** and **current checking balance** to instantly see projected vs. actual performance
- Dual-line **Plotly chart** — projected balance (from opening) vs. actual/forward projection (from today)
- Today marker and $0 line for quick at-a-glance risk assessment
- **Month summary metrics**: opening balance, current balance, variance from projection, total income, total expenses, projected end-of-month balance
- Full **daily ledger** table with color-coded income (green) and expenses (red)

### 🗓️ Tab 2 — Next Month
- Opening balance automatically carried over from the current month's end-of-month projection
- **Override expander** — adjust individual bill amounts and due dates for next month without touching sidebar defaults
- **One-off expenses expander** — add irregular expenses (e.g. a night out, medical bill)
- Credit-card **carry-over** (current balance − statement balance) flows automatically into next month
- Summary metrics: opening, total paychecks, total outgoing, projected end balance
- Fixed expense breakdown table and full daily ledger

### 🏦 Tab 3 — Future Savings
Four sub-tabs for longer-horizon planning:

| Sub-tab | What it shows |
|---|---|
| **💰 Savings Overview** | Current account balances (Ally, Burke, Robinhood, Schwab, Merrill, Checking), progress bar toward a savings goal, pie chart of asset allocation, projected liquid savings over a configurable horizon |
| **🏠 Mortgage Down Payment** | Required down payment at any % for a given home price, months-to-goal calculator, savings progress chart, and a quick reference table of down payment targets across multiple price/% combinations |
| **🚗 Car Payment Schedule** | Full amortization table with optional extra annual payment (e.g. April bonus), total interest paid, payoff date, and stacked area chart of principal vs. interest per payment |
| **📈 401k Projections** | Year-by-year growth projection with IRS elective deferral limits enforced (standard, age 50+ catch-up, and special age 60–63 catch-up), employer match, annual bonus contributions, and an annual contributions breakdown chart |

---

## 🗂️ Project Structure

```
budget-dashboard/
├── app.py                   # Entry point — page config, tabs, title
├── README.md
├── SUPABASE_SETUP.md        # Step-by-step guide for Supabase cloud storage setup
├── data/
│   ├── current_data.csv     # Local storage for sidebar state snapshots
│   └── future_data.csv      # Local storage for future savings snapshots
└── src/
    ├── sidebar.py           # Sidebar UI: income, recurring expenses, credit cards, save button
    ├── tab_current.py       # Tab 1: current-month ledger, chart, summary
    ├── tab_next.py          # Tab 2: next-month ledger, chart, summary
    ├── tab_savings.py       # Tab 3: future savings sub-tabs
    ├── config_io.py         # Persist/load sidebar state (CSV ↔ Supabase)
    ├── future_io.py         # Persist/load future savings state (CSV ↔ Supabase)
    └── utils.py             # Shared helpers: formatting, date utilities, ledger builder
```

---

## ⚙️ Sidebar Configuration

The sidebar is the control panel for the entire dashboard. Changes here flow into both the current-month and next-month tabs.

### 💵 Income
| Field | Description |
|---|---|
| Paycheck Amount | Dollar amount per paycheck |
| Pay Frequency | Weekly (choose day-of-week) or Monthly (choose day-of-month) |

### 💸 Additional Income *(expandable)*
Add one-time income items for the current month (bonus, reimbursement, side work) with a description, amount, and day of the month it lands.

### 📉 Recurring Expenses *(expandable)*
Each item has an **amount** and a **due day of the month**.

**Housing & Utilities**
- Rent, Parking, Gas, Electricity, Water, Sewage

**Bills & Subscriptions**
- Student Loans, Internet, Phone, Insurance, Subscriptions

### 🧾 Additional One-Time Expenses *(expandable)*
Non-recurring expenses for the current month (car repair, medical bill, etc.) with a name, amount, and day.

### 💳 Credit Cards *(expandable per card)*
Each card tracks:
| Field | Description |
|---|---|
| Statement Balance | Amount due this month (paid in Tab 1) |
| Current Balance | Live running balance (leave 0 if same as statement) |
| Due Day | Day of month the statement is due |

The difference between **Current Balance − Statement Balance** is automatically treated as a carry-over payment in Tab 2 (next month).

### 💾 Save All Changes
Persists the entire sidebar state as a new timestamped snapshot. The active storage backend is shown beneath the button.

---

## 🗃️ Data Persistence

The app uses an **append-only snapshot** model — every save creates a new timestamped row and the app always reads the latest one. This means you have a full history of every saved state.

### Storage Backends

| Environment | Backend | File / Table |
|---|---|---|
| Local (default) | CSV | `current_data.csv`, `future_data.csv` |
| Cloud / Local with secrets | Supabase PostgreSQL | `budget_snapshots`, `future_snapshots` |

Backend detection is automatic:
- If `SUPABASE_URL` is present in `st.secrets` and is not a placeholder, Supabase is used.
- Otherwise, the app falls back to local CSV files — no configuration needed for local development.

### Smart State Restoration
When the app loads, the latest snapshot is restored into `st.session_state`. Month-specific fields (additional income, one-time expenses) are **automatically cleared** when the saved snapshot is from a prior calendar month, so you start each month with a clean slate while keeping all recurring bills and income settings intact.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/budget-dashboard.git
   cd budget-dashboard
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**
   ```bash
   streamlit run app.py
   ```

4. Open your browser to `http://localhost:8501`

---

## ☁️ Cloud Storage (Supabase) — Optional

To persist your budget data in the cloud (useful when deploying to Streamlit Community Cloud), follow the full setup instructions in [`SUPABASE_SETUP.md`](SUPABASE_SETUP.md).

**Quick summary:**

1. Create a free project at [supabase.com](https://supabase.com)
2. Run the SQL in `SUPABASE_SETUP.md` to create the `budget_snapshots` and `future_snapshots` tables
3. Add your credentials to `.streamlit/secrets.toml`:
   ```toml
   SUPABASE_URL = "https://your-project-id.supabase.co"
   SUPABASE_KEY = "your-anon-or-service-role-key"
   ```
4. Re-run the app — the backend indicator in the sidebar will switch to **☁️ Supabase**

> ⚠️ Never commit `.streamlit/secrets.toml` to version control. Add it to `.gitignore`.

---

## 🚢 Deploying to Streamlit Community Cloud

1. Push your repo to GitHub (without secrets)
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo
3. Set `app.py` as the main file
4. Add your `SUPABASE_URL` and `SUPABASE_KEY` in **Settings → Secrets**

The app will automatically use Supabase for storage when deployed.

---

## 🧱 Module Reference

### `app.py`
Entry point. Sets page config (`wide` layout, 💰 icon), renders the title and date caption, calls `build_sidebar()`, and creates the three main tabs.

### `sidebar.py`
Renders the full sidebar and initialises all `st.session_state` keys. Loads the latest snapshot from storage on first run. Contains five internal sections: `_section_income`, `_section_additional_income`, `_section_recurring_expenses`, `_section_one_time_expenses`, and `_section_credit_cards`.

### `tab_current.py`
Builds the current-month expense list from session state, constructs a daily ledger via `build_ledger()`, overlays an actual-balance projection from today, and renders a Plotly dual-line chart plus a styled DataFrame ledger.

### `tab_next.py`
Mirrors `tab_current.py` for the following month. Adds an override expander (per-bill amount/day overrides that don't touch sidebar defaults), a one-off expenses expander, and displays a fixed expense breakdown table alongside the ledger.

### `tab_savings.py`
Hosts four sub-tabs: Savings Overview, Mortgage Down Payment Calculator, Car Loan Amortization, and 401k Projections. Loads and saves state via `future_io.py`.

### `config_io.py`
Handles reading and writing the **sidebar / current-month** state. Public API:
- `load_latest()` — returns the latest snapshot dict (or `None`)
- `save_current(state)` — persists the current session state
- `apply_to_state(row)` — writes a snapshot dict into `st.session_state`
- `is_cloud()` — returns `True` when Supabase is the active backend

### `future_io.py`
Handles reading and writing the **future savings** state. Mirrors `config_io.py` with an identical public API (`load_future_latest`, `save_future`, `apply_future_to_state`) and a separate `FUTURE_DEFAULTS` dict used as fallback values throughout `tab_savings.py`.

### `utils.py`
Shared utilities:
- `fmt(val)` — formats a float as a USD string (e.g. `$1,234.56`)
- `get_days_of_week(year, month, weekday)` — returns all dates in a month that fall on a given weekday
- `get_paydays(year, month)` — returns payday dates based on sidebar frequency settings
- `get_weekly_expense_days(year, month, key)` — returns dates for weekly recurring expenses
- `build_ledger(year, month, expenses, opening_balance)` — builds a day-by-day `pd.DataFrame` ledger with running balance

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | UI framework |
| `pandas` | Data manipulation, CSV I/O |
| `plotly` | Interactive charts |
| `supabase` *(optional)* | Cloud storage backend |

---

## 🔒 Security Notes

- All data is stored locally in CSV files by default — no account or internet connection required.
- Supabase credentials are read from `st.secrets` and are never stored in code.
- The snapshot model means no data is ever overwritten; you can recover any prior state by reading earlier rows from the CSV or Supabase table.

---

## 📄 License

This project is for personal use. Feel free to fork and adapt it for your own budgeting needs.
