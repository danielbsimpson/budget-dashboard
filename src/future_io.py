"""
future_io.py – Persist and load Future Savings tab defaults.

Backend is chosen automatically (same logic as config_io.py):
  • LOCAL  → future_data.csv  (append-only, last row wins)
  • CLOUD  → Supabase table `future_snapshots`

Column reference:
  saved_at              – ISO-8601 timestamp

  -- Savings Overview --
  ally                  – float
  burke                 – float
  rh                    – float  (Robin Hood)
  schwab                – float
  merill                – float
  sav_checking          – float
  sav_goal              – float
  monthly_save          – float
  sav_months            – int

  -- Mortgage Down Payment --
  hp                    – float  (home price)
  dp_pct                – int    (down payment %)
  dp_saved              – float
  dp_monthly            – float

  -- Car Loan --
  car_bal               – float
  car_rate              – float
  car_pay               – float
  car_extra             – float
  car_start             – text   (ISO date e.g. "2025-09-01")

  -- 401k --
  k401_cur              – float
  k401_sal              – float
  k401_pct              – int
  k401_emp              – int
  k401_growth           – int
  k401_bonus            – float
  k401_age              – int
  k401_retire           – int

  -- Student Loans --
  sl_bal1               – float  (Loan 1: Direct Grad PLUS current balance)
  sl_rate1              – float  (Loan 1: annual interest rate %)
  sl_bal2               – float  (Loan 2: Direct Unsubsidized current balance)
  sl_rate2              – float  (Loan 2: annual interest rate %)
  sl_pay1               – float  (monthly payment allocated to Loan 1; remainder goes to Loan 2)
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

FUTURE_PATH     = Path(__file__).parent.parent / "data" / "future_data.csv"
_SUPA_TABLE     = "future_snapshots"

# ─────────────────────────────────────────────────────────────────────────────
# Stable column order
# ─────────────────────────────────────────────────────────────────────────────

FUTURE_COLS = [
    "saved_at",
    # Savings Overview
    "ally", "burke", "rh", "schwab", "merill",
    "sav_checking", "sav_goal", "monthly_save", "sav_months",
    # Mortgage
    "hp", "dp_pct", "dp_saved", "dp_monthly",
    # Car
    "car_bal", "car_rate", "car_pay", "car_extra", "car_start",
    # 401k
    "k401_cur", "k401_sal", "k401_pct", "k401_emp",
    "k401_growth", "k401_bonus", "k401_age", "k401_retire",
    # Student Loans
    "sl_bal1", "sl_rate1",
    "sl_bal2", "sl_rate2",
    "sl_pay1",
]

# Default values (mirrors hardcoded values in tab_savings.py)
FUTURE_DEFAULTS: dict = {
    "ally":         1025.0,
    "burke":        3700.0,
    "rh":            843.0,
    "schwab":      23700.0,
    "merill":      37000.0,
    "sav_checking": 2883.84,
    "sav_goal":    49122.0,
    "monthly_save":  800.0,
    "sav_months":     24,
    "hp":         300000.0,
    "dp_pct":         10,
    "dp_saved":     5725.0,
    "dp_monthly":    500.0,
    "car_bal":     33051.81,
    "car_rate":        6.0,
    "car_pay":       650.0,
    "car_extra":    1000.0,
    "car_start":  "2025-09-01",
    "k401_cur":    4923.80,
    "k401_sal":   75000.0,
    "k401_pct":       10,
    "k401_emp":        4,
    "k401_growth":     6,
    "k401_bonus":  5000.0,
    "k401_age":       36,
    "k401_retire":    65,
    # Student Loans
    # Loan 1: Direct Grad PLUS
    "sl_bal1":   6561.77,
    "sl_rate1":     6.83,
    # Loan 2: Direct Loan - Unsubsidized
    "sl_bal2":  14031.70,
    "sl_rate2":     5.83,
    # Monthly payment allocated to Loan 1 (remainder auto-assigned to Loan 2)
    "sl_pay1":    226.77,
}


# ─────────────────────────────────────────────────────────────────────────────
# Backend detection (re-uses the same secrets as config_io)
# ─────────────────────────────────────────────────────────────────────────────

def _use_supabase() -> bool:
    try:
        url = st.secrets.get("SUPABASE_URL", "")
        return bool(url) and "your-project-id" not in url
    except Exception:
        return False


@st.cache_resource(show_spinner=False)
def _supabase_client():
    from supabase import create_client  # type: ignore[import]
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


# ─────────────────────────────────────────────────────────────────────────────
# Snapshot builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_snapshot(state) -> dict:
    """Flatten the Future Savings session_state keys into one storable dict."""
    row: dict = {"saved_at": datetime.now().isoformat(timespec="seconds")}
    for key in FUTURE_COLS[1:]:          # skip "saved_at"
        val = state.get(key, FUTURE_DEFAULTS.get(key))
        # date_input widgets return a date object; store as ISO string
        if isinstance(val, date):
            val = val.isoformat()
        row[key] = val
    return row


# ─────────────────────────────────────────────────────────────────────────────
# CSV backend
# ─────────────────────────────────────────────────────────────────────────────

def _csv_load_latest() -> dict | None:
    if not FUTURE_PATH.exists():
        return None
    try:
        df = pd.read_csv(FUTURE_PATH, dtype=str)
    except Exception:
        return None
    if df.empty:
        return None
    return dict(df.iloc[-1])


def _csv_save(row: dict) -> None:
    new_df = pd.DataFrame([row], columns=FUTURE_COLS)
    if FUTURE_PATH.exists():
        existing = pd.read_csv(FUTURE_PATH, dtype=str)
        # Ensure any newly added columns exist in old data
        for col in FUTURE_COLS:
            if col not in existing.columns:
                existing[col] = None
        out = pd.concat([existing[FUTURE_COLS], new_df], ignore_index=True)
    else:
        out = new_df
    out.to_csv(FUTURE_PATH, index=False)


# ─────────────────────────────────────────────────────────────────────────────
# Supabase backend
# ─────────────────────────────────────────────────────────────────────────────

def _supa_load_latest() -> dict | None:
    try:
        client = _supabase_client()
        resp = (
            client.table(_SUPA_TABLE)
            .select("*")
            .order("saved_at", desc=True)
            .limit(1)
            .execute()
        )
        if resp.data:
            return resp.data[0]
    except Exception as exc:
        st.warning(f"⚠️ Supabase read (future) failed — falling back to CSV. ({exc})")
        return _csv_load_latest()
    return None


def _supa_save(row: dict) -> None:
    try:
        client = _supabase_client()
        client.table(_SUPA_TABLE).insert(row).execute()
    except Exception as exc:
        st.warning(f"⚠️ Supabase write (future) failed — saved to CSV instead. ({exc})")
        _csv_save(row)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def load_future_latest() -> dict | None:
    """Return the most-recently-saved Future Savings snapshot, or None."""
    if _use_supabase():
        return _supa_load_latest()
    return _csv_load_latest()


def save_future(state) -> None:
    """Persist current Future Savings session_state to CSV or Supabase."""
    row = _build_snapshot(state)
    if _use_supabase():
        _supa_save(row)
    else:
        _csv_save(row)


def apply_future_to_state(row: dict) -> None:
    """
    Write a Future snapshot row into st.session_state.
    Only sets keys not already present this session.
    """
    def _float(v, default=0.0):
        try:
            return float(v)
        except (TypeError, ValueError):
            return default

    def _int(v, default=0):
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return default

    def _date(v, default: date) -> date:
        try:
            return date.fromisoformat(str(v))
        except (ValueError, TypeError):
            return default

    mapping = {
        # key          : (converter,  default_value)
        "ally":         (_float, FUTURE_DEFAULTS["ally"]),
        "burke":        (_float, FUTURE_DEFAULTS["burke"]),
        "rh":           (_float, FUTURE_DEFAULTS["rh"]),
        "schwab":       (_float, FUTURE_DEFAULTS["schwab"]),
        "merill":       (_float, FUTURE_DEFAULTS["merill"]),
        "sav_checking": (_float, FUTURE_DEFAULTS["sav_checking"]),
        "sav_goal":     (_float, FUTURE_DEFAULTS["sav_goal"]),
        "monthly_save": (_float, FUTURE_DEFAULTS["monthly_save"]),
        "sav_months":   (_int,   FUTURE_DEFAULTS["sav_months"]),
        "hp":           (_float, FUTURE_DEFAULTS["hp"]),
        "dp_pct":       (_int,   FUTURE_DEFAULTS["dp_pct"]),
        "dp_saved":     (_float, FUTURE_DEFAULTS["dp_saved"]),
        "dp_monthly":   (_float, FUTURE_DEFAULTS["dp_monthly"]),
        "car_bal":      (_float, FUTURE_DEFAULTS["car_bal"]),
        "car_rate":     (_float, FUTURE_DEFAULTS["car_rate"]),
        "car_pay":      (_float, FUTURE_DEFAULTS["car_pay"]),
        "car_extra":    (_float, FUTURE_DEFAULTS["car_extra"]),
        "k401_cur":     (_float, FUTURE_DEFAULTS["k401_cur"]),
        "k401_sal":     (_float, FUTURE_DEFAULTS["k401_sal"]),
        "k401_pct":     (_int,   FUTURE_DEFAULTS["k401_pct"]),
        "k401_emp":     (_int,   FUTURE_DEFAULTS["k401_emp"]),
        "k401_growth":  (_int,   FUTURE_DEFAULTS["k401_growth"]),
        "k401_bonus":   (_float, FUTURE_DEFAULTS["k401_bonus"]),
        "k401_age":     (_int,   FUTURE_DEFAULTS["k401_age"]),
        "k401_retire":  (_int,   FUTURE_DEFAULTS["k401_retire"]),
        # Student Loans
        "sl_bal1":      (_float, FUTURE_DEFAULTS["sl_bal1"]),
        "sl_rate1":     (_float, FUTURE_DEFAULTS["sl_rate1"]),
        "sl_bal2":      (_float, FUTURE_DEFAULTS["sl_bal2"]),
        "sl_rate2":     (_float, FUTURE_DEFAULTS["sl_rate2"]),
        "sl_pay1":      (_float, FUTURE_DEFAULTS["sl_pay1"]),
    }

    for key, (converter, default) in mapping.items():
        if key not in st.session_state:
            st.session_state[key] = converter(row.get(key), default)

    # car_start is a date — handle separately
    if "car_start" not in st.session_state:
        st.session_state["car_start"] = _date(
            row.get("car_start"), date.fromisoformat(FUTURE_DEFAULTS["car_start"])
        )
