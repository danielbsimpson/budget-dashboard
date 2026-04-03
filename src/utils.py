"""
utils.py – Shared helpers: formatting, date utilities, ledger builder.
"""
from __future__ import annotations

import calendar
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

_EASTERN = ZoneInfo("America/New_York")


def now_eastern() -> datetime:
    """Return the current datetime in US Eastern time (ET/EST/EDT)."""
    return datetime.now(tz=_EASTERN)


def today_eastern() -> date:
    """Return today's date in US Eastern time."""
    return now_eastern().date()


# ─────────────────────────────────────────────────────────────────────────────
# Formatting
# ─────────────────────────────────────────────────────────────────────────────

def fmt(val: float) -> str:
    """Format a float as a USD currency string."""
    return f"${val:,.2f}"


# ─────────────────────────────────────────────────────────────────────────────
# Date helpers
# ─────────────────────────────────────────────────────────────────────────────

WEEKDAY_NAMES = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
]


def get_days_of_week(year: int, month: int, weekday: int) -> list[date]:
    """Return all dates in *month* that fall on *weekday* (0 = Mon … 6 = Sun)."""
    _, days_in_month = calendar.monthrange(year, month)
    return [
        date(year, month, d)
        for d in range(1, days_in_month + 1)
        if date(year, month, d).weekday() == weekday
    ]


def get_paydays(year: int, month: int) -> list[date]:
    """Return payday dates for *month* based on sidebar session_state settings."""
    freq = st.session_state.get("pay_frequency", "Weekly")
    if freq == "Weekly":
        weekday = st.session_state.get("pay_weekday_idx", 4)   # default Friday
        return get_days_of_week(year, month, weekday)
    # Monthly – single payment on the chosen day-of-month
    day = st.session_state.get("pay_monthly_day", 1)
    _, days_in_month = calendar.monthrange(year, month)
    return [date(year, month, min(day, days_in_month))]


def get_weekly_expense_days(year: int, month: int, key: str) -> list[date]:
    """Return all dates in *month* matching the weekday stored in session_state[key]['weekday']."""
    entry = st.session_state.get(key, {})
    weekday = entry.get("weekday", 0) if isinstance(entry, dict) else 0
    return get_days_of_week(year, month, weekday)


# ─────────────────────────────────────────────────────────────────────────────
# Ledger builder
# ─────────────────────────────────────────────────────────────────────────────

def build_ledger(
    year: int,
    month: int,
    expenses: list[dict],
    opening_balance: float,
) -> pd.DataFrame:
    """
    Build a daily ledger for *month* — **one row per calendar day**.

    ``expenses`` items:
        ``date``        – :class:`datetime.date`
        ``description`` – str
        ``amount``      – float  (positive = outflow, negative = inflow)

    Returned columns:
        Date, Day, Description, Amount, Running Balance
    """
    _, days_in_month = calendar.monthrange(year, month)

    exp_by_date: dict[date, list] = {}
    for e in expenses:
        exp_by_date.setdefault(e["date"], []).append(e)

    rows: list[dict] = []
    running = opening_balance

    for d in range(1, days_in_month + 1):
        day = date(year, month, d)
        day_items = exp_by_date.get(day, [])

        if day_items:
            income_items  = [e for e in day_items if e["amount"] < 0]
            expense_items = [e for e in day_items if e["amount"] >= 0]
            day_net = sum(e["amount"] for e in day_items)
            running -= day_net   # positive = outflow

            parts: list[str] = []
            if income_items:
                names = ", ".join(e["description"] for e in income_items)
                total = sum(abs(e["amount"]) for e in income_items)
                parts.append(f"⬆ {names} (+${total:,.2f})")
            if expense_items:
                names = ", ".join(e["description"] for e in expense_items)
                total = sum(e["amount"] for e in expense_items)
                parts.append(f"⬇ {names} (-${total:,.2f})")

            rows.append({
                "Date":            day,
                "Day":             day.strftime("%A"),
                "Description":     "  |  ".join(parts),
                "Amount":          day_net,
                "Running Balance": running,
            })
        else:
            rows.append({
                "Date":            day,
                "Day":             day.strftime("%A"),
                "Description":     "—",
                "Amount":          0.0,
                "Running Balance": running,
            })

    return pd.DataFrame(rows)
