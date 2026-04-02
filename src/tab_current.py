"""
tab_current.py – Tab 1: Current Month budget, chart, and ledger.
"""
from __future__ import annotations

import calendar
import datetime as _dt
from datetime import date

import plotly.graph_objects as go
import streamlit as st

from sidebar import REC_DEFAULTS
from utils import build_ledger, fmt, get_paydays, get_weekly_expense_days


# ─────────────────────────────────────────────────────────────────────────────
# Expense-list builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_expenses(year: int, month: int, days_in_month: int) -> list[dict]:
    """Assemble every scheduled transaction for *month* from session_state."""
    expenses: list[dict] = []
    paycheck_amt = st.session_state.get("paycheck_amount", 1490.00)

    # ── Paydays ──────────────────────────────────────────────────────────────
    for pay_day in get_paydays(year, month):
        expenses.append({"date": pay_day, "description": "Payday 💰", "amount": -paycheck_amt})

    # ── Weekly expenses ───────────────────────────────────────────────────────
    def _wk_amt(key: str, default: float) -> float:
        v = st.session_state.get(key, {})
        return v.get("amount", default) if isinstance(v, dict) else default

    car_amt = _wk_amt("wk_car", 150.00)
    for d in get_weekly_expense_days(year, month, "wk_car"):
        expenses.append({"date": d, "description": "Car Payment", "amount": car_amt})

    grocery_amt = _wk_amt("wk_grocery", 120.00)
    for d in get_weekly_expense_days(year, month, "wk_grocery"):
        expenses.append({"date": d, "description": "Grocery", "amount": grocery_amt})

    # ── Recurring bills ───────────────────────────────────────────────────────
    for key in REC_DEFAULTS:
        entry = st.session_state.get(key, {})
        if isinstance(entry, dict):
            expenses.append({
                "date":        date(year, month, min(int(entry.get("day", 1)), days_in_month)),
                "description": REC_DEFAULTS[key]["label"],
                "amount":      float(entry.get("amount", 0.0)),
            })

    # ── Additional income ─────────────────────────────────────────────────────
    for row in st.session_state.get("add_income_rows", []):
        expenses.append({
            "date":        date(year, month, min(int(row.get("day", 1)), days_in_month)),
            "description": row.get("description", "Additional Income"),
            "amount":      -float(row.get("amount", 0.0)),
        })

    # ── One-off expenses (tab-level, legacy key) ─────────────────────────────
    for row in st.session_state.get("oe_rows", []):
        expenses.append({
            "date":        date(year, month, min(int(row.get("day", 1)), days_in_month)),
            "description": row.get("description", "One-Off Expense"),
            "amount":      float(row.get("amount", 0.0)),
        })

    # ── Additional one-time expenses (sidebar, saved to CSV) ─────────────────
    for row in st.session_state.get("oe_expense_rows", []):
        if row.get("name", "").strip():
            expenses.append({
                "date":        date(year, month, min(int(row.get("day", 1)), days_in_month)),
                "description": row.get("name", "One-Time Expense"),
                "amount":      float(row.get("amount", 0.0)),
            })

    # ── Credit-card statement payments ────────────────────────────────────────
    for card in st.session_state.get("cc_cards", []):
        amount = float(card.get("statement_balance", 0.0))
        if amount > 0:
            expenses.append({
                "date":        date(year, month, min(int(card.get("pay_day", 1)), days_in_month)),
                "description": f"{card.get('name', 'Card')} Payment",
                "amount":      amount,
            })

    return expenses


# ─────────────────────────────────────────────────────────────────────────────
# Actual-balance projection
# ─────────────────────────────────────────────────────────────────────────────

def _add_actual_column(df, current_balance: float, today: date) -> float:
    """
    Append a 'Running Balance (Actual)' column to *df* in-place.

    Returns the last non-None value (projected end-of-month from current balance).
    """
    net_by_date: dict[date, float] = {}
    # Re-derive from the ledger's own Amount column (already collapsed per-day)
    for _, row in df.iterrows():
        net_by_date[row["Date"]] = row["Amount"]

    actual_col: list = []
    running = current_balance

    for row_date in df["Date"]:
        if row_date < today:
            actual_col.append(None)
        elif row_date == today:
            actual_col.append(current_balance)
            running = current_balance
        else:
            running -= net_by_date.get(row_date, 0.0)
            actual_col.append(running)

    df["Running Balance (Actual)"] = actual_col
    projected_eom = next((v for v in reversed(actual_col) if v is not None), current_balance)
    return projected_eom


# ─────────────────────────────────────────────────────────────────────────────
# Chart
# ─────────────────────────────────────────────────────────────────────────────

def _render_chart(df, today: date, month: int, year: int) -> None:
    eod_proj = (
        df.groupby("Date", sort=True)["Running Balance"].last().reset_index()
    )
    eod_actual = (
        df.groupby("Date", sort=True)["Running Balance (Actual)"].last().reset_index()
    )

    proj_dates   = eod_proj["Date"].tolist()
    proj_balance = eod_proj["Running Balance"].tolist()
    actual_bal   = eod_actual["Running Balance (Actual)"].tolist()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=proj_dates, y=proj_balance,
        mode="lines+markers", name="Projected (from opening)",
        line=dict(color="#aaaaaa", width=2, dash="dot"), marker=dict(size=4),
        hovertemplate="%{x|%b %d}: <b>%{y:$,.2f}</b><extra>Projected</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=proj_dates, y=actual_bal,
        mode="lines+markers", name="Actual / Forward Projection",
        line=dict(color="#1f77b4", width=3), marker=dict(size=6),
        connectgaps=False,
        hovertemplate="%{x|%b %d}: <b>%{y:$,.2f}</b><extra>Actual/Forward</extra>",
    ))

    fig.add_hline(y=0, line_dash="dash", line_color="red",
                  annotation_text="$0", annotation_position="bottom right")
    fig.add_vline(
        x=_dt.datetime(today.year, today.month, today.day).timestamp() * 1000,
        line_dash="dot", line_color="orange",
        annotation_text="Today", annotation_position="top right",
    )

    fig.update_layout(
        title=f"Checking Account Balance — {today.strftime('%B %Y')}",
        xaxis_title="Date", yaxis_title="Balance ($)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        yaxis=dict(tickprefix="$", tickformat=",.0f"),
    )
    st.plotly_chart(fig, width='stretch')


# ─────────────────────────────────────────────────────────────────────────────
# Ledger table
# ─────────────────────────────────────────────────────────────────────────────

def _render_ledger(df) -> None:
    st.subheader("📒 Daily Ledger")

    def _color_balance(val):
        if val == "—":
            return "color: gray"
        try:
            return "color: green" if float(val) >= 0 else "color: red"
        except (ValueError, TypeError):
            return "color: gray"

    def _color_amount(val):
        try:
            v = float(val)
            if v < 0:   return "color: green"
            if v > 0:   return "color: red"
        except (ValueError, TypeError):
            pass
        return "color: gray"

    display = df.copy()
    display["Date"] = display["Date"].apply(lambda d: d.strftime("%a, %b %d"))
    display["Running Balance (Actual)"] = display["Running Balance (Actual)"].apply(
        lambda v: "—" if v is None else f"${v:,.2f}"
    )

    styled = (
        display.style
        .map(_color_balance, subset=["Running Balance", "Running Balance (Actual)"])
        .map(_color_amount,  subset=["Amount"])
        .format({"Amount": "${:,.2f}", "Running Balance": "${:,.2f}"})
    )
    st.dataframe(styled, width='stretch', height=600)


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def tab_current_month() -> None:
    today = date.today()
    year, month = today.year, today.month
    _, days_in_month = calendar.monthrange(year, month)

    st.header(f"📅 {today.strftime('%B %Y')} Budget")

    col_ob, col_cb = st.columns(2)
    with col_ob:
        opening_balance = st.number_input(
            "Opening Checking Balance ($)",
            help="Your balance at the start of the month (day 1).",
            value=st.session_state.get("cm_opening", 0.0),
            step=0.01, format="%.2f", key="cm_opening",
        )
    with col_cb:
        current_balance = st.number_input(
            "Current Checking Balance ($)",
            help="Your actual balance right now. Used to project the rest of the month from today.",
            value=st.session_state.get("cm_current_bal", opening_balance),
            step=0.01, format="%.2f", key="cm_current_bal",
        )

    # Build data
    expenses = _build_expenses(year, month, days_in_month)
    df = build_ledger(year, month, expenses, opening_balance)
    projected_eom = _add_actual_column(df, current_balance, today)

    # Persist for Tab 2
    st.session_state["cm_projected_eom"] = projected_eom

    # Summary values
    total_income   = -sum(e["amount"] for e in expenses if e["amount"] < 0)
    total_expenses =  sum(e["amount"] for e in expenses if e["amount"] > 0)

    eod_proj = df.groupby("Date", sort=True)["Running Balance"].last().reset_index()
    today_rows = eod_proj[eod_proj["Date"] == today]
    projected_today = float(today_rows["Running Balance"].values[0]) if not today_rows.empty else None
    variance = (current_balance - projected_today) if projected_today is not None else 0.0

    # Chart
    _render_chart(df, today, month, year)

    # Summary metrics
    st.subheader("📊 Month Summary")
    mc1, mc2, mc3, mc4, mc5, mc6 = st.columns(6)
    mc1.metric("Opening Balance",          fmt(opening_balance))
    mc2.metric("Current Balance",          fmt(current_balance),
               delta=f"{variance:+,.2f} vs projected", delta_color="normal")
    mc3.metric("Projected Today",          fmt(projected_today) if projected_today is not None else "—")
    mc4.metric("Total Income",             fmt(total_income))
    mc5.metric("Total Expenses",           fmt(total_expenses))
    mc6.metric("Projected End (from now)", fmt(projected_eom),
               delta=f"{projected_eom - opening_balance:+,.2f} vs opening", delta_color="normal")

    if variance >= 0:
        st.success(f"✅ You are **{fmt(variance)} ahead** of the projected balance for today.")
    else:
        st.warning(f"⚠️ You are **{fmt(abs(variance))} behind** the projected balance for today.")

    _render_ledger(df)
