"""
config_io.py – Persist and load all sidebar input defaults.

Backend is chosen automatically:
  • LOCAL  (default) → current_data.csv  (append-only, last row wins)
  • CLOUD  (Streamlit Community Cloud) → Supabase table `budget_snapshots`

Detection logic:
  If st.secrets contains a non-placeholder SUPABASE_URL the Supabase backend
  is used; otherwise the CSV backend is used.  This means the app works
  out-of-the-box locally with no Supabase account needed.

Supabase table schema – see SUPABASE_SETUP.md for the full SQL.

CSV / Supabase column reference:
  saved_at              – ISO-8601 timestamp of the save
  paycheck_amount       – float
  pay_frequency         – "Weekly" | "Monthly"
  pay_weekday_idx       – int (0=Mon … 6=Sun); used when Weekly
  pay_monthly_day       – int (1-31); used when Monthly
  opening_balance       – float  (Opening Checking Balance, day 1 of month)
  current_balance       – float  (Current Checking Balance, as of last save)
  rec_<key>_amount      – float  } one pair per each REC_KEY
  rec_<key>_day         – int    }
  ai_rows               – JSON text  list[{description, amount, day}]
  oe_expense_rows       – JSON text  list[{name, amount, day}]
  cc_cards              – JSON text  list[{name, statement_balance,
                                           current_balance, pay_day}]

The store keeps every snapshot ever saved; the app always reads the latest.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).parent.parent / "data" / "current_data.csv"
_SUPABASE_TABLE = "budget_snapshots"

# Keys for all recurring expense fields
REC_KEYS = [
    "rec_rent", "rec_parking", "rec_gas", "rec_elec",
    "rec_water", "rec_sewer", "rec_student", "rec_internet",
    "rec_phone", "rec_insurance", "rec_subs",
]

# ─────────────────────────────────────────────────────────────────────────────
# Backend detection
# ─────────────────────────────────────────────────────────────────────────────

def _use_supabase() -> bool:
    """
    Return True when a real (non-placeholder) SUPABASE_URL is present in
    st.secrets.  Falls back to False (CSV) on any error so local dev always
    works without credentials.
    """
    try:
        url = st.secrets.get("SUPABASE_URL", "")
        return bool(url) and "your-project-id" not in url
    except Exception:
        return False


@st.cache_resource(show_spinner=False)
def _supabase_client():
    """Return a cached Supabase client (imported lazily so local dev never
    needs the package unless Supabase is actually configured)."""
    from supabase import create_client  # type: ignore[import]
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def is_cloud() -> bool:
    """Public helper — True when the Supabase backend is active."""
    return _use_supabase()


# ─────────────────────────────────────────────────────────────────────────────
# Build the flat column list so the CSV always has a stable schema
# ─────────────────────────────────────────────────────────────────────────────

SCALAR_COLS = [
    "saved_at",
    "paycheck_amount",
    "pay_frequency",
    "pay_weekday_idx",
    "pay_monthly_day",
    "opening_balance",
    "current_balance",
]
for _k in REC_KEYS:
    SCALAR_COLS.append(f"{_k}_amount")
    SCALAR_COLS.append(f"{_k}_day")
SCALAR_COLS += ["ai_rows", "oe_expense_rows", "cc_cards"]


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers – build a snapshot dict from session_state
# ─────────────────────────────────────────────────────────────────────────────

def _build_snapshot(state) -> dict:
    """Flatten session_state into a single storable dict."""
    row: dict = {"saved_at": datetime.now().isoformat(timespec="seconds")}
    row["paycheck_amount"] = state.get("paycheck_amount", 1490.00)
    row["pay_frequency"]   = state.get("pay_frequency",   "Weekly")
    row["pay_weekday_idx"] = state.get("pay_weekday_idx", 4)
    row["pay_monthly_day"] = state.get("pay_monthly_day", 1)
    row["opening_balance"] = state.get("cm_opening",      0.0)
    row["current_balance"] = state.get("cm_current_bal",  0.0)
    for key in REC_KEYS:
        entry = state.get(key, {})
        if isinstance(entry, dict):
            row[f"{key}_amount"] = entry.get("amount", 0.0)
            row[f"{key}_day"]    = entry.get("day",    1)
        else:
            row[f"{key}_amount"] = 0.0
            row[f"{key}_day"]    = 1
    row["ai_rows"]         = json.dumps(state.get("add_income_rows",  []))
    row["oe_expense_rows"] = json.dumps(state.get("oe_expense_rows",  []))
    row["cc_cards"]        = json.dumps(state.get("cc_cards",         []))
    return row


# ─────────────────────────────────────────────────────────────────────────────
# CSV backend
# ─────────────────────────────────────────────────────────────────────────────

def _csv_load_latest() -> dict | None:
    if not DATA_PATH.exists():
        return None
    try:
        df = pd.read_csv(DATA_PATH, dtype=str)
    except Exception:
        return None
    if df.empty:
        return None
    return dict(df.iloc[-1])


def _csv_save(row: dict) -> None:
    new_df = pd.DataFrame([row], columns=SCALAR_COLS)
    if DATA_PATH.exists():
        existing = pd.read_csv(DATA_PATH, dtype=str)
        out = pd.concat([existing, new_df], ignore_index=True)
    else:
        out = new_df
    out.to_csv(DATA_PATH, index=False)


# ─────────────────────────────────────────────────────────────────────────────
# Supabase backend
# ─────────────────────────────────────────────────────────────────────────────

def _supa_load_latest() -> dict | None:
    try:
        client = _supabase_client()
        resp = (
            client.table(_SUPABASE_TABLE)
            .select("*")
            .order("saved_at", desc=True)
            .limit(1)
            .execute()
        )
        if resp.data:
            return resp.data[0]
    except Exception as exc:
        st.warning(f"⚠️ Supabase read failed — falling back to CSV. ({exc})")
        return _csv_load_latest()
    return None


def _supa_save(row: dict) -> None:
    try:
        client = _supabase_client()
        client.table(_SUPABASE_TABLE).insert(row).execute()
    except Exception as exc:
        st.warning(f"⚠️ Supabase write failed — saved to CSV instead. ({exc})")
        _csv_save(row)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def load_latest() -> dict | None:
    """
    Return the most-recently-saved snapshot as a plain dict, or None.
    Reads from Supabase when deployed, CSV when local.
    """
    if _use_supabase():
        return _supa_load_latest()
    return _csv_load_latest()


def save_current(state) -> None:
    """
    Persist the current session_state as a new snapshot.
    Writes to Supabase when deployed, CSV when local.
    """
    row = _build_snapshot(state)
    if _use_supabase():
        _supa_save(row)
    else:
        _csv_save(row)


def apply_to_state(row: dict) -> None:
    """
    Write a CSV row (as returned by load_latest) into st.session_state.
    Only sets keys that have not already been set this session.
    Month-specific fields (additional income, one-time expenses) are cleared
    automatically when the save originated from a prior calendar month.
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

    # ── Determine whether the last save was in the current calendar month ────
    try:
        saved_dt   = datetime.fromisoformat(row.get("saved_at", ""))
        now        = datetime.now()
        same_month = (saved_dt.year == now.year and saved_dt.month == now.month)
    except (ValueError, TypeError):
        same_month = False

    # ── Scalars ──────────────────────────────────────────────────────────────
    if "paycheck_amount" not in st.session_state:
        st.session_state["paycheck_amount"] = _float(row.get("paycheck_amount"), 1490.00)

    if "pay_frequency" not in st.session_state:
        st.session_state["pay_frequency"] = str(row.get("pay_frequency", "Weekly"))

    if "pay_weekday_idx" not in st.session_state:
        st.session_state["pay_weekday_idx"] = _int(row.get("pay_weekday_idx"), 4)

    if "pay_monthly_day" not in st.session_state:
        st.session_state["pay_monthly_day"] = _int(row.get("pay_monthly_day"), 1)

    if "cm_opening" not in st.session_state:
        st.session_state["cm_opening"] = _float(row.get("opening_balance"), 0.0)

    if "cm_current_bal" not in st.session_state:
        st.session_state["cm_current_bal"] = _float(row.get("current_balance"), 0.0)

    # ── Recurring expenses ────────────────────────────────────────────────────
    for key in REC_KEYS:
        if key not in st.session_state:
            st.session_state[key] = {
                "amount": _float(row.get(f"{key}_amount"), 0.0),
                "day":    _int(row.get(f"{key}_day"),    1),
            }

    # ── Additional income rows (month-specific) ───────────────────────────────
    if "add_income_rows" not in st.session_state:
        if same_month:
            raw = row.get("ai_rows", "[]")
            try:
                parsed = json.loads(raw) if isinstance(raw, str) else []
                st.session_state["add_income_rows"] = parsed if isinstance(parsed, list) else []
            except (json.JSONDecodeError, TypeError):
                st.session_state["add_income_rows"] = []
        else:
            # New month — discard last month's additional income
            st.session_state["add_income_rows"] = []

    # ── One-time expense rows (month-specific) ────────────────────────────────
    if "oe_expense_rows" not in st.session_state:
        if same_month:
            raw = row.get("oe_expense_rows", "[]")
            try:
                parsed = json.loads(raw) if isinstance(raw, str) else []
                st.session_state["oe_expense_rows"] = parsed if isinstance(parsed, list) else []
            except (json.JSONDecodeError, TypeError):
                st.session_state["oe_expense_rows"] = []
        else:
            # New month — discard last month's one-time expenses
            st.session_state["oe_expense_rows"] = []

    # ── Credit cards ──────────────────────────────────────────────────────────
    if "cc_cards" not in st.session_state:
        raw = row.get("cc_cards", "[]")
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else []
            st.session_state["cc_cards"] = parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            st.session_state["cc_cards"] = []
