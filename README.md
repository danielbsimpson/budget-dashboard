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
├── app.py                    # Entry point — page config, tabs, title
├── requirements.txt          # Python dependencies for local and cloud deployment
├── README.md
├── SUPABASE_SETUP.md         # Step-by-step guide for Supabase cloud storage setup
├── archived_data/            # Legacy CSV/Excel sheets (not used by the app)
├── data/
│   ├── current_data.csv      # Local storage for sidebar state snapshots
│   └── future_data.csv       # Local storage for future savings snapshots
└── src/
    ├── sidebar.py            # Sidebar UI: income, recurring expenses, credit cards, save button
    ├── tab_current.py        # Tab 1: current-month ledger, chart, summary
    ├── tab_next.py           # Tab 2: next-month ledger, chart, summary
    ├── tab_savings.py        # Tab 3: future savings sub-tabs
    ├── config_io.py          # Persist/load sidebar state (CSV ↔ Supabase)
    ├── future_io.py          # Persist/load future savings state (CSV ↔ Supabase)
    └── utils.py              # Shared helpers: formatting, date utilities, ledger builder
```

> `app.py` lives at the root because Streamlit requires the entry point to be runnable from the repo root. It prepends `src/` to `sys.path` at startup so all module imports resolve correctly.

---

## ⚙️ Sidebar Configuration

The sidebar is the control panel for the entire dashboard. Changes here flow into both the current-month and next-month tabs automatically.

### 💵 Income
| Field | Description |
|---|---|
| Paycheck Amount | Dollar amount per paycheck |
| Pay Frequency | **Weekly** — choose the day of the week; **Monthly** — choose the day of the month |

### 💸 Additional Income *(expandable)*
Add one-time income items for the current month (bonus, reimbursement, side work, etc.) — each with a description, amount, and the day of the month it is received.

### 📉 Recurring Expenses *(expandable)*
Each item stores an **amount** and a **due day of the month**.

**🏠 Housing & Utilities**
- Rent, Parking, Gas, Electricity, Water, Sewage

**📡 Bills & Subscriptions**
- Student Loans, Internet, Phone, Insurance, Subscriptions

> **Weekly expenses** — Car Payment and Groceries are also included in both ledgers as recurring weekly outflows. Their amounts are read from `wk_car` and `wk_grocery` in session state (defaults: $150 and $120 respectively). These are currently hardcoded defaults and are not exposed as sidebar inputs.

### 🧾 Additional One-Time Expenses *(expandable)*
Non-recurring expenses for the current month (car repair, medical bill, etc.) with a name, amount, and day. These are saved to the snapshot and cleared automatically at month rollover.

### 💳 Credit Cards *(expandable per card)*
Each card tracks:

| Field | Description |
|---|---|
| Card Name | Display name for the card |
| Statement Balance | Amount on the last statement — due this month (Tab 1) |
| Current Balance | Live running balance right now (leave `0` if same as statement) |
| Due Day | Day of month the statement balance is due |

The difference **Current Balance − Statement Balance** is automatically carried over as an additional payment in Tab 2 (next month). Cards can be added or removed dynamically.

### 💾 Save All Changes
Persists the entire sidebar state as a new timestamped snapshot. The active storage backend (`📄 local CSV` or `☁️ Supabase`) is displayed beneath the button.

---

## 🗃️ Data Persistence

The app uses an **append-only snapshot** model — every save creates a new timestamped row and the app always reads the most recent one. This gives you a full history of every saved state.

### Storage Backends

| Environment | Backend | File / Table |
|---|---|---|
| Local (default) | CSV | `data/current_data.csv`, `data/future_data.csv` |
| Cloud / Local with secrets configured | Supabase PostgreSQL | `budget_snapshots`, `future_snapshots` |

Backend detection is automatic:
- If `SUPABASE_URL` is present in `st.secrets` and is **not** a placeholder value, Supabase is used.
- Otherwise the app falls back to local CSV — no configuration needed for local development.

### Smart State Restoration
On first load each session, the latest snapshot is restored into `st.session_state`. Month-specific fields (additional income, one-time expenses) are **automatically cleared** when the snapshot originates from a prior calendar month, so you start each month with a clean slate while retaining all recurring bills, income settings, and credit card configuration.

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

To persist your budget data in the cloud (required when deploying to Streamlit Community Cloud, since the filesystem is ephemeral), follow the full setup guide in [`SUPABASE_SETUP.md`](SUPABASE_SETUP.md).

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

1. Push your repo to GitHub (**without** `.streamlit/secrets.toml`)
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repository
3. Set **`app.py`** as the main file
4. Go to **Settings → Secrets** and paste your Supabase credentials:
   ```toml
   SUPABASE_URL = "https://your-project-id.supabase.co"
   SUPABASE_KEY = "your-anon-or-service-role-key"
   ```

The app will automatically detect the Supabase credentials and use cloud storage. Without them it will still run, but any saves will only persist for the current session (Streamlit Cloud has an ephemeral filesystem).

---

## 📝 Recommended `.gitignore`

```gitignore
# Streamlit secrets (never commit credentials)
.streamlit/secrets.toml

# Python cache
__pycache__/
*.pyc

# Local data files (optional — omit if you want to track your CSV history in git)
data/current_data.csv
data/future_data.csv
```

---

## 🧱 Module Reference

### `app.py` *(root)*
Entry point. Prepends `src/` to `sys.path`, sets page config (`wide` layout, 💰 icon), renders the title and date caption, calls `build_sidebar()`, and creates the three main tabs.

### `src/sidebar.py`
Renders the full sidebar and initialises all `st.session_state` keys. Loads the latest snapshot from storage once per session. Contains five internal sections:
- `_section_income` — paycheck amount and pay frequency
- `_section_additional_income` — expandable one-time income rows
- `_section_recurring_expenses` — housing/utilities and bills/subscriptions expanders
- `_section_one_time_expenses` — expandable one-time expense rows
- `_section_credit_cards` — per-card expanders with statement/current balance inputs

### `src/tab_current.py`
Assembles the current month's expense list from session state (paydays, weekly car/grocery expenses, all recurring bills, additional income, one-time expenses, and credit card payments), builds a daily ledger via `build_ledger()`, overlays an actual-balance projection from today's current balance, and renders a Plotly dual-line chart plus a styled DataFrame ledger.

### `src/tab_next.py`
Mirrors `tab_current.py` for the following calendar month. Adds:
- An override expander (per-bill amount/day adjustments that don't touch sidebar defaults)
- A one-off expenses expander (pre-seeded with a "Date Night / Fun" example)
- A fixed expense breakdown table
- Credit-card carry-over (current − statement) included automatically

### `src/tab_savings.py`
Hosts four sub-tabs for longer-horizon planning. Loads defaults from `future_io.py` once per session and provides a **💾 Save Future Savings Defaults** button at the bottom.

### `src/config_io.py`
Handles reading and writing the **sidebar / current-month** state. CSV path resolves to `data/current_data.csv` relative to the repo root. Public API:
- `load_latest()` — returns the latest snapshot dict, or `None`
- `save_current(state)` — flattens `st.session_state` and appends a new snapshot row
- `apply_to_state(row)` — writes a snapshot dict into `st.session_state`, respecting month-rollover logic
- `is_cloud()` — returns `True` when the Supabase backend is active

### `src/future_io.py`
Handles reading and writing the **future savings** state. CSV path resolves to `data/future_data.csv` relative to the repo root. Exports `FUTURE_DEFAULTS` — a dict of fallback values used throughout `tab_savings.py`. Public API mirrors `config_io.py`: `load_future_latest`, `save_future`, `apply_future_to_state`.

### `src/utils.py`
Shared utilities used across all tab modules:
- `fmt(val)` — formats a float as a USD string, e.g. `$1,234.56`
- `get_days_of_week(year, month, weekday)` — returns all dates in a month that fall on a given weekday (0 = Monday … 6 = Sunday)
- `get_paydays(year, month)` — returns payday dates for a month based on the sidebar's frequency/day settings
- `get_weekly_expense_days(year, month, key)` — returns all dates in a month matching the weekday stored in `session_state[key]["weekday"]`
- `build_ledger(year, month, expenses, opening_balance)` — builds a day-by-day `pd.DataFrame` with columns: `Date`, `Day`, `Description`, `Amount`, `Running Balance`

---

## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| `streamlit` | `==1.55.0` | UI framework |
| `pandas` | `==2.3.3` | Data manipulation, CSV I/O |
| `plotly` | `==6.6.0` | Interactive charts (`plotly.express` + `plotly.graph_objects`) |
| `supabase` | `>=2.0.0` | Cloud storage backend *(optional — only needed with Supabase credentials)* |

All other imports (`sys`, `json`, `os`, `calendar`, `datetime`, `pathlib`) are Python standard library.

---

## 🔒 Security Notes

- All data is stored locally in CSV files by default — no account or internet connection required.
- Supabase credentials are read exclusively from `st.secrets` and are never stored in source code.
- The append-only snapshot model means no data is ever overwritten; any prior state can be recovered by reading earlier rows from the CSV or Supabase table.
- The `supabase` package is imported lazily (inside the function that creates the client), so it is never loaded unless Supabase is actually configured — local installs without the package work without errors.

---

## 📄 License

This project is for personal use. Feel free to fork and adapt it for your own budgeting needs.

