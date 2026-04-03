"""
tab_next.py – Tab 2: Next Month budget, chart, summary, and ledger.
"""
from __future__ import annotations

import calendar
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from utils import fmt, get_paydays, get_weekly_expense_days, today_eastern


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _rec_amt(key: str, default: float) -> float:
    v = st.session_state.get(key, {})
    return v.get("amount", default) if isinstance(v, dict) else default


def _rec_day(key: str, default: int) -> int:
    v = st.session_state.get(key, {})
    return int(v.get("day", default)) if isinstance(v, dict) else default


# ─────────────────────────────────────────────────────────────────────────────
# Optional overrides expander
# ─────────────────────────────────────────────────────────────────────────────

def _overrides_expander(rec: dict, days: dict) -> tuple[dict, dict]:
    """
    Render the optional per-field override expander.
    Returns updated (rec, days) dicts.
    """
    with st.expander("🔧 Override amounts & due dates for this month (optional)", expanded=False):
        st.caption("Changes here only affect the next-month ledger, not the sidebar defaults.")
        overrideable = [
            ("rec_gas",       "Gas"),
            ("rec_elec",      "Electricity"),
            ("rec_water",     "Water"),
            ("rec_sewer",     "Sewage"),
            ("rec_internet",  "Internet"),
            ("rec_phone",     "Phone"),
            ("rec_student",   "Student Loans"),
            ("rec_insurance", "Insurance"),
            ("rec_subs",      "Subscriptions"),
        ]
        for key, lbl in overrideable:
            ca, cd = st.columns([2, 1])
            with ca:
                rec[key] = st.number_input(
                    f"{lbl} ($)", value=rec[key], step=0.01, format="%.2f",
                    key=f"nm_ov_{key}_amt")
            with cd:
                days[key] = st.number_input(
                    "Day", value=days[key], min_value=1, max_value=31, step=1,
                    key=f"nm_ov_{key}_day")
    return rec, days


# ─────────────────────────────────────────────────────────────────────────────
# One-off expenses expander
# ─────────────────────────────────────────────────────────────────────────────

def _one_offs_expander() -> None:
    if "nm_oe_rows" not in st.session_state:
        st.session_state.nm_oe_rows = [
            {"description": "Date Night / Fun", "amount": 150.0, "day": 15}
        ]

    def _add():
        st.session_state.nm_oe_rows.append({"description": "", "amount": 0.0, "day": 1})

    def _del(i: int):
        st.session_state.nm_oe_rows.pop(i)

    with st.expander("📋 Additional One-Off Expenses (optional)", expanded=False):
        st.caption("Extra or irregular expenses for next month only.")
        for i, row in enumerate(st.session_state.nm_oe_rows):
            # Migrate legacy rows that stored a date object
            if "date" in row and "day" not in row:
                st.session_state.nm_oe_rows[i]["day"] = row["date"].day
                del st.session_state.nm_oe_rows[i]["date"]
                row = st.session_state.nm_oe_rows[i]
            c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
            with c1:
                st.session_state.nm_oe_rows[i]["description"] = st.text_input(
                    f"NM Expense #{i+1}", value=row["description"], key=f"nm_oe_desc_{i}")
            with c2:
                st.session_state.nm_oe_rows[i]["amount"] = st.number_input(
                    f"NM Amount #{i+1}", value=float(row["amount"]),
                    step=0.01, format="%.2f", key=f"nm_oe_amt_{i}")
            with c3:
                st.session_state.nm_oe_rows[i]["day"] = st.number_input(
                    f"Day #{i+1}", value=int(row.get("day", 1)),
                    min_value=1, max_value=31, step=1, key=f"nm_oe_day_{i}")
            with c4:
                st.button("🗑️", key=f"nm_oe_del_{i}", on_click=_del, args=(i,))
        st.button("➕ Add Expense", on_click=_add, key="nm_add_oe")


# ─────────────────────────────────────────────────────────────────────────────
# Expense-list builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_expenses(year: int, month: int, days_in_month: int,
                    rec: dict, days: dict, paycheck_amt: float) -> list[dict]:
    expenses: list[dict] = []

    # Paydays
    for pay_day in get_paydays(year, month):
        expenses.append({"date": pay_day, "description": "Payday 💰", "amount": -paycheck_amt})

    # Weekly
    def _wk_amt(key: str, default: float) -> float:
        v = st.session_state.get(key, {})
        return v.get("amount", default) if isinstance(v, dict) else default

    car_amt = _wk_amt("wk_car", 150.00)
    for d in get_weekly_expense_days(year, month, "wk_car"):
        expenses.append({"date": d, "description": "Car Payment", "amount": car_amt})

    grocery_amt = _wk_amt("wk_grocery", 120.00)
    for d in get_weekly_expense_days(year, month, "wk_grocery"):
        expenses.append({"date": d, "description": "Grocery", "amount": grocery_amt})

    # Fixed recurring bills
    housing_day = days.get("rec_rent", 2)
    bill_map = [
        ("rec_rent",      "Rent",          housing_day),
        ("rec_parking",   "Parking",        housing_day),
        ("rec_gas",       "Gas",            days["rec_gas"]),
        ("rec_elec",      "Electricity",    days["rec_elec"]),
        ("rec_water",     "Water",          days["rec_water"]),
        ("rec_sewer",     "Sewage",         days["rec_sewer"]),
        ("rec_student",   "Student Loans",  days["rec_student"]),
        ("rec_subs",      "Subscriptions",  days["rec_subs"]),
        ("rec_internet",  "Internet",       days["rec_internet"]),
        ("rec_phone",     "Phone",          days["rec_phone"]),
        ("rec_insurance", "Insurance",      days["rec_insurance"]),
    ]
    for key, label, day in bill_map:
        expenses.append({
            "date":        date(year, month, min(day, days_in_month)),
            "description": label,
            "amount":      rec[key],
        })

    # Credit-card carry-over
    for card in st.session_state.get("cc_cards", []):
        stmt  = float(card.get("statement_balance", 0.0))
        curr  = float(card.get("current_balance",  0.0))
        carry = max(curr - stmt, 0.0) if curr > 0 else 0.0
        if carry > 0:
            pay_date = date(year, month, min(int(card.get("pay_day", 15)), days_in_month))
            expenses.append({"date": pay_date, "description": f"{card['name']} carry-over",
                             "amount": carry})

    # One-off extras (tab-level, session only)
    for row in st.session_state.get("nm_oe_rows", []):
        if row.get("description", "").strip():
            expenses.append({
                "date":        date(year, month, min(int(row.get("day", 1)), days_in_month)),
                "description": row["description"],
                "amount":      float(row["amount"]),
            })

    expenses.sort(key=lambda x: x["date"])
    return expenses


# ─────────────────────────────────────────────────────────────────────────────
# Ledger builder (next-month variant — keeps descriptive multi-item rows)
# ─────────────────────────────────────────────────────────────────────────────

def _build_ledger_nm(year: int, month: int, days_in_month: int,
                     expenses: list[dict], nm_opening: float) -> pd.DataFrame:
    exp_by_date: dict = {}
    for e in expenses:
        exp_by_date.setdefault(e["date"], []).append(e)

    rows: list[dict] = []
    running = nm_opening

    for d in range(1, days_in_month + 1):
        day = date(year, month, d)
        day_expenses = exp_by_date.get(day, [])
        if day_expenses:
            income_items  = [e for e in day_expenses if e["amount"] < 0]
            expense_items = [e for e in day_expenses if e["amount"] >= 0]
            day_net = sum(e["amount"] for e in day_expenses)
            running -= day_net

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
                "Date":            day.strftime("%A, %b %d"),
                "Description":     "  |  ".join(parts),
                "Amount":          day_net,
                "Running Balance": running,
            })
        else:
            rows.append({
                "Date":            day.strftime("%A, %b %d"),
                "Description":     "—",
                "Amount":          0.0,
                "Running Balance": running,
            })

    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def tab_next_month() -> None:
    st.header("🗓️ Next Month Budget")
    st.markdown(
        "Recurring bills and CC carry-over are pulled from the sidebar. "
        "The **Statement Balance** on each card is paid off this month; "
        "the **carry-over** (current − statement) is due next month."
    )

    today = today_eastern()
    next_month_date = (date(today.year, today.month, 1) + timedelta(days=32)).replace(day=1)
    year, month = next_month_date.year, next_month_date.month
    _, days_in_month = calendar.monthrange(year, month)

    # Opening balance = end-of-month projection from Tab 1
    nm_opening = float(st.session_state.get("cm_projected_eom", 0.0))
    st.info(
        f"**{calendar.month_name[month]} {year}** — "
        f"Opening balance: **{fmt(nm_opening)}** "
        f"(end-of-{calendar.month_name[today.month]} projected from your current balance)"
    )

    # Recurring amounts & days (start from sidebar values)
    rec = {
        "rec_rent":      _rec_amt("rec_rent",      2898.00),
        "rec_parking":   _rec_amt("rec_parking",     75.00),
        "rec_gas":       _rec_amt("rec_gas",          85.00),
        "rec_elec":      _rec_amt("rec_elec",        100.00),
        "rec_water":     _rec_amt("rec_water",        55.00),
        "rec_sewer":     _rec_amt("rec_sewer",       120.00),
        "rec_internet":  _rec_amt("rec_internet",     69.99),
        "rec_phone":     _rec_amt("rec_phone",        90.04),
        "rec_student":   _rec_amt("rec_student",     423.00),
        "rec_insurance": _rec_amt("rec_insurance",   150.00),
        "rec_subs":      _rec_amt("rec_subs",         47.00),
    }
    days = {
        "rec_rent":      _rec_day("rec_rent",      2),
        "rec_parking":   _rec_day("rec_parking",   2),
        "rec_gas":       _rec_day("rec_gas",        2),
        "rec_elec":      _rec_day("rec_elec",       2),
        "rec_water":     _rec_day("rec_water",      2),
        "rec_sewer":     _rec_day("rec_sewer",      2),
        "rec_internet":  _rec_day("rec_internet",  26),
        "rec_phone":     _rec_day("rec_phone",     29),
        "rec_student":   _rec_day("rec_student",   10),
        "rec_insurance": _rec_day("rec_insurance",  3),
        "rec_subs":      _rec_day("rec_subs",      24),
    }

    rec, days = _overrides_expander(rec, days)
    _one_offs_expander()

    cc_cards = st.session_state.get("cc_cards", [])
    cc_carry_total = sum(
        max(c.get("current_balance", 0.0) - c.get("statement_balance", 0.0), 0.0)
        for c in cc_cards
    )
    rent_total = (rec["rec_rent"] + rec["rec_parking"] + rec["rec_gas"]
                  + rec["rec_elec"] + rec["rec_water"] + rec["rec_sewer"])

    paycheck_amt = st.session_state.get("paycheck_amount", 1490.00)
    expenses = _build_expenses(year, month, days_in_month, rec, days, paycheck_amt)
    df = _build_ledger_nm(year, month, days_in_month, expenses, nm_opening)

    total_income = sum(abs(e["amount"]) for e in expenses if e["amount"] < 0)
    total_out    = sum(e["amount"]      for e in expenses if e["amount"] > 0)
    running      = df["Running Balance"].iloc[-1] if not df.empty else nm_opening
    rent_covered = (nm_opening + total_income) >= (rent_total + cc_carry_total)

    # ── Chart ─────────────────────────────────────────────────────────────────
    st.divider()
    st.subheader("📈 Balance Over Time")
    chart_df = df.drop_duplicates(subset="Date", keep="last").copy()
    fig = px.line(chart_df, x="Date", y="Running Balance", markers=True,
                  title=f"{calendar.month_name[month]} {year} — Projected Checking Balance")
    fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="$0")
    fig.add_hline(y=rec["rec_rent"] + rec["rec_parking"], line_dash="dot",
                  line_color="orange", annotation_text="Rent + Parking")
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, width='stretch', key="chart_next_balance")

    # ── Summary ───────────────────────────────────────────────────────────────
    st.subheader("📊 Next Month Summary")
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Opening Balance",       fmt(nm_opening))
    mc2.metric("Total Paychecks",       fmt(total_income))
    mc3.metric("Total Outgoing",        fmt(total_out))
    mc4.metric("Projected End Balance", fmt(running),
               delta=f"{running - nm_opening:+,.2f}")

    if rent_covered:
        st.success(f"✅ All fixed expenses covered. Projected end balance: {fmt(running)}")
    else:
        shortfall = (rent_total + cc_carry_total) - (nm_opening + total_income)
        st.error(f"⚠️ Shortfall of {fmt(shortfall)} — rent + CC carry-over may not be covered!")


    # ── Ledger ────────────────────────────────────────────────────────────────
    st.subheader("📒 Daily Ledger")

    def _color_balance(val):
        return "color: green" if val >= 0 else "color: red"

    def _color_amount(val):
        if val < 0:   return "color: green"
        if val > 0:   return "color: red"
        return ""

    styled = (
        df.style
        .map(_color_balance, subset=["Running Balance"])
        .map(_color_amount,  subset=["Amount"])
        .format({"Amount": "${:,.2f}", "Running Balance": "${:,.2f}"})
    )
    st.dataframe(styled, width='stretch', height=600, hide_index=True)

    # ── Fixed expense breakdown ───────────────────────────────────────────────
    with st.expander("💡 Fixed Expense Breakdown", expanded=False):
        breakdown_items: list[tuple] = [
            ("Rent",          rec["rec_rent"]),
            ("Parking",       rec["rec_parking"]),
            ("Gas",           rec["rec_gas"]),
            ("Electricity",   rec["rec_elec"]),
            ("Water",         rec["rec_water"]),
            ("Sewage",        rec["rec_sewer"]),
            ("Internet",      rec["rec_internet"]),
            ("Phone",         rec["rec_phone"]),
            ("Student Loans", rec["rec_student"]),
            ("Insurance",     rec["rec_insurance"]),
            ("Subscriptions", rec["rec_subs"]),
        ]
        for card in cc_cards:
            stmt  = float(card.get("statement_balance", 0.0))
            curr  = float(card.get("current_balance",  0.0))
            carry = max(curr - stmt, 0.0) if curr > 0 else 0.0
            breakdown_items.append((f"{card['name']} carry-over (current − statement)", carry))
        breakdown_items.append(("— Total CC carry-over (due next month)", cc_carry_total))

        bd_df = pd.DataFrame(breakdown_items, columns=["Item", "Amount"])
        bd_df["Amount"] = bd_df["Amount"].map(lambda v: f"${v:,.2f}")
        st.dataframe(bd_df, width='stretch', hide_index=True)

