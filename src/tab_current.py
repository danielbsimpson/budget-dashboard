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
from utils import build_ledger, fmt, get_days_of_week, get_paydays, today_eastern


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
    for wk_row in st.session_state.get("weekly_expense_rows", []):
        amt     = float(wk_row.get("amount", 0.0))
        weekday = int(wk_row.get("weekday", 0))
        name    = wk_row.get("name", "Weekly Expense")
        for d in get_days_of_week(year, month, weekday):
            expenses.append({"date": d, "description": name, "amount": amt})

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
    st.plotly_chart(fig, width='stretch', key="chart_current_balance")


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
    st.dataframe(styled, width='stretch', height=600, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def tab_current_month() -> None:
    today = today_eastern()
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

    # ── Summary tile colours ──────────────────────────────────────────────────
    RENT_THRESHOLD = 2898.00

    # Opening Balance: green if >$100 above rent threshold, yellow if within
    # $100, red if more than $100 below.
    ob_diff = opening_balance - RENT_THRESHOLD
    if ob_diff > 100:
        ob_color = "#1e7e34"       # green
    elif ob_diff >= -100:
        ob_color = "#856404"       # yellow/amber
    else:
        ob_color = "#721c24"       # red

    # Current Balance: green unless projected_eom ≤ 100 (yellow) or ≤ 0 (red)
    if projected_eom <= 0:
        cb_color = "#721c24"
    elif projected_eom <= 100:
        cb_color = "#856404"
    else:
        cb_color = "#1e7e34"

    # Projected Today: green if projected <= current (we're at or ahead of
    # schedule), red if projected > current (we're behind).
    if projected_today is None:
        pt_color = "#1e7e34"
    elif projected_today > current_balance:
        pt_color = "#721c24"
    else:
        pt_color = "#1e7e34"

    # Total Income: always green
    ti_color = "#1e7e34"

    # Total Expenses: always red
    te_color = "#721c24"

    # Projected End: compare against rent-related bills (rent + parking +
    # water + sewage) to ensure next month's day-2 payments are covered.
    rent_entry    = st.session_state.get("rec_rent",    {})
    parking_entry = st.session_state.get("rec_parking", {})
    water_entry   = st.session_state.get("rec_water",   {})
    sewer_entry   = st.session_state.get("rec_sewer",   {})
    next_rent_total = (
        float(rent_entry.get("amount",    0.0) if isinstance(rent_entry,    dict) else 0.0)
        + float(parking_entry.get("amount", 0.0) if isinstance(parking_entry, dict) else 0.0)
        + float(water_entry.get("amount",   0.0) if isinstance(water_entry,   dict) else 0.0)
        + float(sewer_entry.get("amount",   0.0) if isinstance(sewer_entry,   dict) else 0.0)
    )
    pe_diff = projected_eom - next_rent_total
    if pe_diff > 100:
        pe_color = "#1e7e34"
    elif pe_diff >= -100:
        pe_color = "#856404"
    else:
        pe_color = "#721c24"

    # ── Render tiles ──────────────────────────────────────────────────────────
    def _tile(label: str, value: str, subtitle: str, bg: str) -> str:
        return f"""
        <div style="
            background:{bg};
            border-radius:10px;
            padding:16px 12px 12px 12px;
            text-align:center;
            color:#ffffff;
            height:100%;
            box-sizing:border-box;
        ">
            <div style="font-size:0.72rem;font-weight:600;letter-spacing:0.05em;
                        text-transform:uppercase;opacity:0.85;margin-bottom:6px;">
                {label}
            </div>
            <div style="font-size:1.45rem;font-weight:700;line-height:1.2;">
                {value}
            </div>
            <div style="font-size:0.72rem;opacity:0.75;margin-top:6px;">
                {subtitle}
            </div>
        </div>"""

    variance_sign = "+" if variance >= 0 else ""
    pt_sub = (
        f"{variance_sign}{variance:,.2f} vs projected"
        if projected_today is not None else "—"
    )

    st.subheader("📊 Month Summary")
    t1, t2, t3, t4, t5, t6 = st.columns(6)
    t1.markdown(_tile(
        "Opening Balance",
        fmt(opening_balance),
        f"{ob_diff:+,.2f} vs rent threshold",
        ob_color,
    ), unsafe_allow_html=True)
    t2.markdown(_tile(
        "Current Balance",
        fmt(current_balance),
        f"Projected end: {fmt(projected_eom)}",
        cb_color,
    ), unsafe_allow_html=True)
    t3.markdown(_tile(
        "Projected Today",
        fmt(projected_today) if projected_today is not None else "—",
        pt_sub,
        pt_color,
    ), unsafe_allow_html=True)
    t4.markdown(_tile(
        "Total Income",
        fmt(total_income),
        "this month",
        ti_color,
    ), unsafe_allow_html=True)
    t5.markdown(_tile(
        "Total Expenses",
        fmt(total_expenses),
        "this month",
        te_color,
    ), unsafe_allow_html=True)
    t6.markdown(_tile(
        "Projected End",
        fmt(projected_eom),
        f"{pe_diff:+,.2f} vs next rent",
        pe_color,
    ), unsafe_allow_html=True)

    st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)

    if variance >= 0:
        st.success(f"✅ You are **{fmt(variance)} ahead** of the projected balance for today.")
    else:
        st.warning(f"⚠️ You are **{fmt(abs(variance))} behind** the projected balance for today.")

    _render_ledger(df)
